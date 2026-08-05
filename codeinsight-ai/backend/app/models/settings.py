from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Settings(Base):
    """
    One settings row per user, keyed by user_id (matches users.id).
    """

    __tablename__ = "settings"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_ai_model: Mapped[str] = mapped_column(String, default="gemini-flash-latest")
    preferred_language: Mapped[str] = mapped_column(String, default="python")
