from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.db.database import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
