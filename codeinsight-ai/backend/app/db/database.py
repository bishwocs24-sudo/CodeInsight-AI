"""
SQLAlchemy engine and session factory.

Uses the classic dependency-injection pattern: `get_db` is a FastAPI
dependency that yields a session and guarantees it's closed after
the request, even if the handler raises.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
