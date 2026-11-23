from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.staticfiles import StaticFiles

from app.api.routes import auth, automation, github, history, review
from app.api.routes import settings as settings_routes
from app.api.routes import upload, static_analysis
from app.core.auth_limits import redis_client
from app.core.config import get_settings
from app.db.database import Base, engine
from app.models import review as _review_model  # noqa: F401 - ensure model is registered before create_all
from app.models import settings as _settings_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401

app_settings = get_settings()

@asynccontextmanager
async def lifespan(_app):
    if not app_settings.production:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="CodeGuard AI",
    description="AI-powered code review, security, and complexity analysis API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(automation.router)
app.include_router(review.router)
app.include_router(history.router)
app.include_router(github.router)
app.include_router(settings_routes.router)
app.include_router(upload.router)
app.include_router(static_analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        redis_client(app_settings.redis_url).ping()
    except (SQLAlchemyError, RedisError) as exc:
        raise HTTPException(503, "Review infrastructure is unavailable") from exc
    return {"status": "ready"}


if app_settings.public_site_dir:
    # Register last so API routes keep their existing paths.
    app.mount("/", StaticFiles(directory=app_settings.public_site_dir, html=True), name="frontend")
