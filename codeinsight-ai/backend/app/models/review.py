import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Review(Base):
    """
    One AI code review. `results` holds the full structured JSON
    returned by the AI service (summary, strengths, weaknesses,
    bug detection, security findings, refactored code, tests, etc.)
    so the shape can evolve without a migration every time.
    """

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    review_type: Mapped[str] = mapped_column(String, default="review")  # review | refactor | security | explain | tests | complexity

    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    results: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
