from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.settings import Settings
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest

router = APIRouter(tags=["settings"])


def _get_or_create_settings(db: Session, user_id: str) -> Settings:
    settings = db.get(Settings, user_id)
    if settings is None:
        settings = Settings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=SettingsResponse)
def get_settings_route(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_or_create_settings(db, user.id)


@router.patch("/settings", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = _get_or_create_settings(db, user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.delete("/account")
def delete_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Deletes the current user's reviews, settings, and account."""
    ReviewRepository(db).delete_all_for_user(user.id)
    db.query(Settings).filter(Settings.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return {"status": "deleted"}
