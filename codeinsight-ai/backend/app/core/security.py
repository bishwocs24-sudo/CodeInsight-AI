"""
Password hashing (bcrypt) and JWT issuing/verification.

This is a self-contained auth system - no third-party account needed.
For production, swap this for Clerk (see docs/AUTH_SETUP.md); the
get_current_user dependency below is the one seam that would need to
change to verify a Clerk-issued token instead of one we signed ourselves.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str | None) -> bool:
    if hashed is None:
        return False  # OAuth-only account - no password to check against
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, *, expires_at: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expires_at if expires_at is not None else expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class TokenError(Exception):
    pass


def decode_access_token(token: str) -> str:
    """Returns the user_id encoded in the token, or raises TokenError."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    user_id = payload.get("sub")
    if not user_id:
        raise TokenError("Token missing subject")
    return user_id
