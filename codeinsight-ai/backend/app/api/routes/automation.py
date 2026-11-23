import hashlib
import hmac
import json
import re
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import SessionLocal, get_db
from app.models.automation import Feedback, Finding, PullRequest, Repository, ReviewJob, now
from app.models.user import User
from app.platform_review.github_app import NAME, SHA
from app.platform_review.jobs import ACTIVE, serialize_finding
from app.platform_review.pipeline import PROMPT_VERSION
from app.platform_review.sarif import build_sarif
from app.platform_review.scanner import RULE_VERSION, SEMGREP_VERSION

router = APIRouter(prefix="/automation", tags=["review automation"])


class Snippet(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    language: Literal["python", "javascript", "typescript", "c", "cpp"]
    code: str = Field(min_length=1, max_length=40_000)
    tests: str | None = Field(default=None, min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_source(self):
        for text in (self.code, self.tests or ""):
            if "\x00" in text or len(text.encode("utf-8")) > 80_000:
                raise ValueError("Source exceeds UTF-8 limits or contains a null byte")
        if not self.code.strip() or (self.tests is not None and not self.tests.strip()):
            raise ValueError("Source and supplied tests must contain code")
        if self.tests and self.language != "python":
            raise ValueError("Isolated verification currently supports Python unittest")
        return self


class Commit(BaseModel):
    sha: str = Field(pattern=rf"^{SHA.pattern}$")


class GitHubPull(BaseModel):
    number: StrictInt = Field(gt=0)
    head: Commit
    base: Commit
    draft: bool = False


class Installation(BaseModel):
    id: StrictInt = Field(gt=0, le=2**63 - 1)


class GitHubRepository(Installation):
    full_name: str = Field(pattern=rf"^{NAME.pattern}$")


class PullEvent(BaseModel):
    installation: Installation
    repository: GitHubRepository
    pull_request: GitHubPull


class Verdict(BaseModel):
    verdict: Literal["confirmed", "false_positive", "clear"]


def policy():
    settings = get_settings()
    inputs = (RULE_VERSION, SEMGREP_VERSION, PROMPT_VERSION, settings.pr_ai_enabled,
              settings.google_model, settings.github_publish_reviews)
    return hashlib.sha256(repr(inputs).encode()).hexdigest()


def quota(db, owner, *, total, active, github):
    # Serialize quota admission on the owning account in PostgreSQL.
    db.execute(select(User.id).where(User.id == owner).with_for_update()).scalar_one()
    owner_jobs = select(func.count()).select_from(ReviewJob).where(
        ReviewJob.owner_id == owner, ReviewJob.pull_request_id.is_not(None)
        if github else ReviewJob.pull_request_id.is_(None),
    )
    if db.scalar(owner_jobs.where(ReviewJob.created_at >= now() - timedelta(hours=1))) >= total:
        raise HTTPException(429, "Hourly review quota reached", headers={"Retry-After": "3600"})
    if db.scalar(owner_jobs.where(ReviewJob.status.in_(ACTIVE))) >= active:
        raise HTTPException(429, "Active review quota reached", headers={"Retry-After": "30"})


def enqueue_pull(event, delivery):
    settings = get_settings()
    with SessionLocal() as db:
        owner = settings.github_review_owner_id
        if not owner or not db.get(User, owner):
            raise HTTPException(503, "GitHub review operator is unavailable")
        db.execute(select(User.id).where(User.id == owner).with_for_update()).scalar_one()
        job = db.scalar(select(ReviewJob).where(ReviewJob.delivery == delivery))
        if job:
            return {"id": job.id, "duplicate": True}
        incoming = event.repository
        repo = db.get(Repository, incoming.id)
        if repo is None:
            repo = Repository(id=incoming.id, name=incoming.full_name, installation_id=event.installation.id)
            db.add(repo)
            db.flush()
        pr = event.pull_request
        pull = db.scalar(select(PullRequest).where(
            PullRequest.repository_id == repo.id, PullRequest.number == pr.number,
        ))
        if pull is None:
            pull = PullRequest(repository_id=repo.id, number=pr.number)
            db.add(pull)
            db.flush()
        key = policy()
        job = db.scalar(select(ReviewJob).where(
            ReviewJob.pull_request_id == pull.id, ReviewJob.head_sha == pr.head.sha,
            ReviewJob.base_sha == pr.base.sha, ReviewJob.policy == key,
        ))
        if job:
            return {"id": job.id, "duplicate": True}
        quota(db, owner, total=100, active=30, github=True)
        repo.name, repo.installation_id = incoming.full_name, event.installation.id
        job = ReviewJob(owner_id=owner, pull_request_id=pull.id, delivery=delivery,
                        head_sha=pr.head.sha, base_sha=pr.base.sha, policy=key)
        db.add(job)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(ReviewJob).where(ReviewJob.delivery == delivery))
            if existing:
                return {"id": existing.id, "duplicate": True}
            raise
        return {"id": job.id, "duplicate": False}


@router.post("/github/webhook", status_code=202)
async def webhook(request: Request):
    settings = get_settings()
    if not settings.github_webhook_secret or not settings.github_app_id:
        raise HTTPException(503, "GitHub App webhook is disabled")
    signature = request.headers.get("x-hub-signature-256", "")
    if not re.fullmatch(r"sha256=[a-f0-9]{64}", signature):
        raise HTTPException(401, "Invalid webhook signature")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 512_000:
            raise HTTPException(413, "Webhook payload too large")
    expected = "sha256=" + hmac.new(settings.github_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid webhook signature")
    if request.headers.get("x-github-event") != "pull_request":
        return {"ignored": True}
    try:
        raw = json.loads(body)
        if raw.get("action") not in {"opened", "reopened", "synchronize", "ready_for_review"}:
            return {"ignored": True}
        event = PullEvent.model_validate(raw)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(422, "Invalid pull request payload") from exc
    allowed = {item.strip() for item in settings.github_allowed_installations.split(",")}
    if str(event.installation.id) not in allowed:
        raise HTTPException(403, "Installation is outside the configured allowlist")
    if event.pull_request.draft:
        return {"ignored": True}
    delivery = request.headers.get("x-github-delivery", "")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", delivery):
        raise HTTPException(422, "Invalid delivery identifier")
    return await run_in_threadpool(enqueue_pull, event, delivery)


@router.get("/capabilities")
def capabilities(_: User = Depends(get_current_user)):
    settings = get_settings()
    return {"sandbox": settings.sandbox_enabled, "ai": settings.pr_ai_enabled and bool(settings.google_api_key)}


@router.post("/jobs", status_code=202)
def submit(payload: Snippet, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.tests and not get_settings().sandbox_enabled:
        raise HTTPException(409, "Isolated test execution is disabled")
    quota(db, user.id, total=30, active=5, github=False)
    job = ReviewJob(owner_id=user.id, payload=payload.model_dump(), policy=policy())
    db.add(job)
    db.commit()
    return {"id": job.id, "status": job.status}


def summary(job, repo=None, pull=None):
    return {
        "id": job.id, "status": job.status, "attempts": job.attempts,
        "created_at": job.created_at.isoformat() + "Z", "updated_at": job.updated_at.isoformat() + "Z",
        "repository": repo.name if repo else None, "pull_number": pull.number if pull else None,
        "head_sha": job.head_sha, "result": job.result, "error": job.error,
    }


def owned_job(db, user, job_id):
    job = db.get(ReviewJob, job_id)
    if not job or job.owner_id != user.id:
        raise HTTPException(404, "Review job not found")
    return job


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(ReviewJob, Repository, PullRequest)
                      .select_from(ReviewJob)
                      .outerjoin(PullRequest, PullRequest.id == ReviewJob.pull_request_id)
                      .outerjoin(Repository, Repository.id == PullRequest.repository_id)
                      .where(ReviewJob.owner_id == user.id)
                      .order_by(ReviewJob.created_at.desc()).limit(50))
    return [summary(job, repo, pull) for job, repo, pull in rows]


@router.get("/jobs/{job_id}")
def job_detail(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = owned_job(db, user, job_id)
    pull = db.get(PullRequest, job.pull_request_id) if job.pull_request_id else None
    repo = db.get(Repository, pull.repository_id) if pull else None
    findings = db.execute(select(Finding, Feedback.verdict).outerjoin(Feedback)
                          .where(Finding.job_id == job_id).order_by(Finding.id)).all()
    return {**summary(job, repo, pull), "findings": [
        {**serialize_finding(item), "verdict": verdict} for item, verdict in findings
    ]}


@router.post("/jobs/{job_id}/cancel")
def cancel(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_job(db, user, job_id)
    result = db.execute(update(ReviewJob).where(
        ReviewJob.id == job_id, ReviewJob.owner_id == user.id, ReviewJob.status.in_(("queued", "running")),
    ).values(status="cancelled", updated_at=now(), payload=None, lease=None, error=None))
    if not result.rowcount:
        raise HTTPException(409, "Only queued or running jobs can be cancelled")
    db.commit()
    return {"status": "cancelled"}


@router.put("/jobs/{job_id}/findings/{finding_id}/feedback")
def feedback(job_id: str, finding_id: int, payload: Verdict,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_job(db, user, job_id)
    item = db.scalar(select(Finding).where(
        Finding.id == finding_id, Finding.job_id == job_id,
    ).with_for_update())
    if item is None:
        raise HTTPException(404, "Finding not found")
    old = db.get(Feedback, item.id)
    if payload.verdict == "clear":
        if old:
            db.delete(old)
        item.suppressed = False
    else:
        db.merge(Feedback(finding_id=item.id, verdict=payload.verdict))
        item.suppressed = payload.verdict == "false_positive"
    db.commit()
    return {"verdict": payload.verdict}


@router.get("/jobs/{job_id}/sarif")
def sarif(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    detail = job_detail(job_id, db, user)
    return build_sarif(detail["findings"], (detail["result"] or {}).get("ruleset", RULE_VERSION))
