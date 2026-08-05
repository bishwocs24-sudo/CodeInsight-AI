from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, github, history, review
from app.api.routes import settings as settings_routes
from app.api.routes import upload
from app.core.config import get_settings
from app.db.database import Base, engine
from app.models import review as _review_model  # noqa: F401 - ensure model is registered before create_all
from app.models import settings as _settings_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401

app_settings = get_settings()

app = FastAPI(
    title="CodeInsight AI",
    description="AI-powered code review, security, and complexity analysis API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(review.router)
app.include_router(history.router)
app.include_router(github.router)
app.include_router(settings_routes.router)
app.include_router(upload.router)


@app.on_event("startup")
def on_startup():
    # For local dev this creates tables directly. In production, swap
    # this out for Alembic migrations instead of create_all.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
