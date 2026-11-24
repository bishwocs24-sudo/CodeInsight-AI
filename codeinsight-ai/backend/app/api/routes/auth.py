import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.auth_limits import limit_auth
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.services.google_identity import verify_identity
from app.schemas.auth import GoogleExchangeRequest, LoginRequest, SignupRequest, TokenResponse, UserResponse
from app.services.github_oauth_service import GitHubOAuthError, GitHubOAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201, dependencies=[Depends(limit_auth)])
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if not get_settings().signup_enabled:
        raise HTTPException(403, "Account registration is closed")
    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(422, "Password exceeds 72 UTF-8 bytes")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "An account with that email already exists.") from exc
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_auth)])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/options")
def auth_options():
    settings = get_settings()
    return {
        "signup": settings.signup_enabled,
        "github": bool(settings.github_oauth_client_id and settings.github_oauth_client_secret),
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/github/login", dependencies=[Depends(limit_auth)])
def github_login():
    settings = get_settings()
    if not settings.github_oauth_client_id:
        raise HTTPException(
            status_code=503,
            detail="GitHub login isn't configured. Set GITHUB_OAUTH_CLIENT_ID/SECRET in backend/.env - see docs/AUTH_SETUP.md.",
        )
    state = secrets.token_urlsafe(32)
    with GitHubOAuthService() as oauth:
        response = RedirectResponse(oauth.authorize_url(state))
    response.set_cookie(
        "codeguard_oauth_state", state, max_age=600, httponly=True, samesite="lax",
        secure=settings.github_oauth_redirect_uri.startswith("https://"),
        path="/auth/github/callback",
    )
    return response


@router.get("/github/callback", dependencies=[Depends(limit_auth)])
def github_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    settings = get_settings()
    expected = request.cookies.get("codeguard_oauth_state")
    if not expected or not secrets.compare_digest(state.encode(), expected.encode()):
        raise HTTPException(401, "GitHub OAuth state is invalid or expired")
    try:
        with GitHubOAuthService() as oauth:
            access_token = oauth.exchange_code_for_token(code)
            profile = oauth.get_profile(access_token)
    except httpx.HTTPError as exc:
        raise HTTPException(502, "GitHub sign-in is temporarily unavailable") from exc
    except GitHubOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = db.query(User).filter(User.github_id == profile["id"]).first()
    if user is None:
        if not settings.signup_enabled:
            raise HTTPException(403, "Account registration is closed")
        if db.query(User).filter(User.email == profile["email"]).first():
            raise HTTPException(409, "Sign in with the password for your existing account")
        user = User(email=profile["email"], github_id=profile["id"], hashed_password=None)
        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "An account with that email already exists") from exc
        db.refresh(user)

    jwt_token = create_access_token(user.id)
    fragment = urlencode({"token": jwt_token})
    response = RedirectResponse(
        f"{settings.frontend_auth_callback_url}#{fragment}",
        headers={"Referrer-Policy": "no-referrer"},
    )
    response.delete_cookie("codeguard_oauth_state", path="/auth/github/callback")
    return response


@router.post("/google/exchange", response_model=TokenResponse, dependencies=[Depends(limit_auth)])
def google_exchange(payload: GoogleExchangeRequest, db: Session = Depends(get_db)):
    claims = verify_identity(payload.id_token)
    user = db.query(User).filter(User.google_subject == claims["sub"]).first()
    if user is None:
        if not get_settings().signup_enabled:
            raise HTTPException(403, "Account registration is closed")
        user = User(email=claims["email"], google_subject=claims["sub"])
        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            user = db.query(User).filter(User.google_subject == claims["sub"]).first()
            if user is None:
                raise HTTPException(409, "This email already belongs to another account") from exc
    expires = min(int(claims["exp"]), int(time.time()) + 45 * 60)
    return TokenResponse(access_token=create_access_token(user.id, expires_at=expires),
                         user=UserResponse.model_validate(user))
