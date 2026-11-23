import logging
import time
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import delete, select, update

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.models.automation import Feedback, Finding, PullRequest, Repository, ReviewJob, now
from app.platform_review.evidence import EXTENSIONS, Source
from app.platform_review.github_app import GitHubApp, RemoteFailure, StaleReview
from app.platform_review.pipeline import run_review
from app.platform_review.sandbox import verify_python

logger = logging.getLogger(__name__)
ACTIVE = ("queued", "running", "publishing")
TERMINAL = ("completed", "cancelled", "failed", "superseded")
MAX_ATTEMPTS = 3
LEASE_SECONDS = 300
PUBLIC_FIELDS = ("id", "source", "rule_id", "path", "line", "severity", "message",
                 "fingerprint", "evidence_sha256", "suppressed")


def serialize_finding(row):
    return {key: getattr(row, key) for key in PUBLIC_FIELDS}


def ready_jobs():
    with SessionLocal() as db:
        timestamp = now()
        db.execute(update(ReviewJob).where(
            ReviewJob.status.in_(ACTIVE), ReviewJob.available_at <= timestamp,
            ReviewJob.attempts >= MAX_ATTEMPTS,
        ).values(status="failed", error="Worker retry limit reached", updated_at=timestamp,
                 payload=None, lease=None))
        ready = db.scalars(select(ReviewJob.id).where(
            ReviewJob.status.in_(ACTIVE), ReviewJob.available_at <= timestamp,
            ReviewJob.attempts < MAX_ATTEMPTS,
        ).order_by(ReviewJob.available_at).limit(30)).all()
        db.commit()
        return ready


def cleanup():
    cutoff = now() - timedelta(days=get_settings().review_retention_days)
    with SessionLocal.begin() as db:
        db.execute(delete(ReviewJob).where(ReviewJob.status.in_(TERMINAL), ReviewJob.updated_at < cutoff))


def claim(job_id):
    lease = str(uuid4())
    timestamp = now()
    with SessionLocal.begin() as db:
        job = db.get(ReviewJob, job_id)
        if not job or job.status not in ACTIVE:
            return None
        status = "publishing" if job.status == "publishing" else "running"
        claimed = db.execute(update(ReviewJob).where(
            ReviewJob.id == job_id, ReviewJob.status == job.status,
            ReviewJob.available_at <= timestamp, ReviewJob.attempts < MAX_ATTEMPTS,
        ).values(status=status, attempts=ReviewJob.attempts + 1, lease=lease,
                 updated_at=timestamp, available_at=timestamp + timedelta(seconds=LEASE_SECONDS)))
        if not claimed.rowcount:
            return None
    return lease


def save_findings(job_id, lease, rows, result, publishing):
    with SessionLocal.begin() as db:
        active = db.execute(update(ReviewJob).where(
            ReviewJob.id == job_id, ReviewJob.lease == lease, ReviewJob.status == "running",
        ).values(status="publishing" if publishing else "completed", result=result,
                 updated_at=now(), payload=None, error=None, lease=lease if publishing else None))
        if not active.rowcount:
            return False
        job = db.get(ReviewJob, job_id)
        fingerprints = [item["fingerprint"] for item in rows]
        prior_feedback = (
            select(Finding.fingerprint).select_from(Finding)
            .join(ReviewJob, ReviewJob.id == Finding.job_id)
            .join(Feedback, Feedback.finding_id == Finding.id)
            .where(ReviewJob.owner_id == job.owner_id, Finding.fingerprint.in_(fingerprints),
                   Feedback.verdict == "false_positive")
        )
        if job.pull_request_id is None:
            prior_feedback = prior_feedback.where(ReviewJob.pull_request_id.is_(None))
        else:
            pull = db.get(PullRequest, job.pull_request_id)
            prior_feedback = prior_feedback.join(PullRequest).where(
                PullRequest.repository_id == pull.repository_id
            )
        suppressed = set(db.scalars(prior_feedback))
        db.add_all(Finding(job_id=job_id, **item, suppressed=item["fingerprint"] in suppressed)
                   for item in rows)
        return True


def finish(job_id, lease, status, *, error=None, publication=None, retryable=False):
    with SessionLocal.begin() as db:
        job = db.get(ReviewJob, job_id)
        if not job or job.lease != lease:
            return
        timestamp = now()
        retry = retryable and job.attempts < MAX_ATTEMPTS
        values = {"lease": None, "updated_at": timestamp, "error": error}
        if retry:
            values["status"] = "publishing" if job.status == "publishing" else "queued"
            values["available_at"] = timestamp + timedelta(seconds=15 * 2 ** (job.attempts - 1))
        else:
            values.update(status=status, payload=None)
        if publication is not None:
            values["result"] = {**job.result, "publication": publication}
        db.execute(update(ReviewJob).where(ReviewJob.id == job_id, ReviewJob.lease == lease).values(**values))


def execute(job_id):
    lease = claim(job_id)
    if not lease:
        return
    started = time.monotonic()
    try:
        with SessionLocal() as db:
            job = db.get(ReviewJob, job_id)
            if not job or job.lease != lease:
                return
            payload, status, head, base = job.payload, job.status, job.head_sha, job.base_sha
            pull = db.get(PullRequest, job.pull_request_id) if job.pull_request_id else None
            repo = db.get(Repository, pull.repository_id) if pull else None
            target = (repo.name, repo.id, repo.installation_id, pull.number) if repo else None
        if target is None:
            text = payload["code"]
            filename = "submission" + EXTENSIONS[payload["language"]]
            lines = {i: line.removesuffix("\r") for i, line in enumerate(text.split("\n"), 1)}
            findings, result = run_review([Source(filename, text, lines)], 0)
            result["verification"] = {"status": "not_requested"}
            if payload.get("tests"):
                with SessionLocal() as db:
                    active = db.get(ReviewJob, job_id)
                    if not active or active.lease != lease:
                        return
                result["verification"] = verify_python(text, payload["tests"])
            result["duration_ms"] = round((time.monotonic() - started) * 1000)
            save_findings(job_id, lease, findings, result, publishing=False)
            return
        with GitHubApp(*target) as github:
            if status == "running":
                sources, skipped = github.sources(head, base)
                findings, result = run_review(sources, skipped)
                result["duration_ms"] = round((time.monotonic() - started) * 1000)
                if not save_findings(job_id, lease, findings, result, publishing=True):
                    return
            with SessionLocal() as db:
                job = db.get(ReviewJob, job_id)
                if not job or job.lease != lease:
                    return
                findings = [serialize_finding(item) for item in db.scalars(
                    select(Finding).where(Finding.job_id == job_id).order_by(Finding.id))]
            publication = github.publish(job_id, head, base, findings)
            finish(job_id, lease, "completed", publication=publication)
    except StaleReview as exc:
        finish(job_id, lease, "superseded", error=str(exc))
    except RemoteFailure as exc:
        finish(job_id, lease, "failed", error=str(exc), retryable=exc.retryable)
    except Exception:
        logger.exception("Review worker failed for %s", job_id)
        finish(job_id, lease, "failed", error="Internal review error", retryable=True)
