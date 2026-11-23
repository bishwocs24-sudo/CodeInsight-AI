from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import BigInteger, JSON, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Repository(Base):
    __tablename__ = "automation_repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    installation_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(250))


class PullRequest(Base):
    __tablename__ = "automation_pull_requests"
    __table_args__ = (UniqueConstraint("repository_id", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey(Repository.id))
    number: Mapped[int]


class ReviewJob(Base):
    __tablename__ = "automation_jobs"
    __table_args__ = (
        UniqueConstraint("pull_request_id", "head_sha", "base_sha", "policy"),
        Index("ix_automation_jobs_dispatch", "status", "available_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    pull_request_id: Mapped[int | None] = mapped_column(ForeignKey(PullRequest.id))
    delivery: Mapped[str | None] = mapped_column(String(80), unique=True)
    head_sha: Mapped[str | None] = mapped_column(String(40))
    base_sha: Mapped[str | None] = mapped_column(String(40))
    policy: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16), default="queued")
    attempts: Mapped[int] = mapped_column(default=0)
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(300))
    lease: Mapped[str | None] = mapped_column(String(36))
    available_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Finding(Base):
    __tablename__ = "automation_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey(ReviewJob.id, ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(16))
    rule_id: Mapped[str] = mapped_column(String(200))
    path: Mapped[str] = mapped_column(String(500))
    line: Mapped[int]
    severity: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64))
    evidence_sha256: Mapped[str] = mapped_column(String(64))
    suppressed: Mapped[bool] = mapped_column(default=False)


class Feedback(Base):
    __tablename__ = "automation_feedback"

    finding_id: Mapped[int] = mapped_column(ForeignKey(Finding.id, ondelete="CASCADE"), primary_key=True)
    verdict: Mapped[str] = mapped_column(String(20))
