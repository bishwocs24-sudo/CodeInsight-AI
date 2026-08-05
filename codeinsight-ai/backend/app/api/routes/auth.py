from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from app.services.github_oauth_service import GitHubOAuthError, GitHubOAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/github/login")
def github_login():
    settings = get_settings()
    if not settings.github_oauth_client_id:
        raise HTTPException(
            status_code=503,
            detail="GitHub login isn't configured. Set GITHUB_OAUTH_CLIENT_ID/SECRET in backend/.env - see docs/AUTH_SETUP.md.",
        )
    oauth = GitHubOAuthService()
    return RedirectResponse(oauth.authorize_url())


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    settings = get_settings()
    oauth = GitHubOAuthService()

    try:
        access_token = oauth.exchange_code_for_token(code)
        profile = oauth.get_profile(access_token)
    except GitHubOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = db.query(User).filter(User.github_id == profile["id"]).first()
    if user is None:
        # No account linked to this GitHub id yet - match by email, or create one.
        user = db.query(User).filter(User.email == profile["email"]).first()
        if user is None:
            user = User(email=profile["email"], github_id=profile["id"], hashed_password=None)
            db.add(user)
        else:
            user.github_id = profile["id"]
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(user.id)
    return RedirectResponse(f"{settings.frontend_auth_callback_url}?token={jwt_token}")
