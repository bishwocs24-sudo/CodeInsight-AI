import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # Nullable because GitHub-OAuth users never set a password.
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    github_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
