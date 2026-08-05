"""
Central application configuration.

All environment-driven settings live here so nothing is hardcoded
inside routes or services. Values are read from a .env file in
local dev, or from real environment variables in production.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://codeinsight:codeinsight@localhost:5432/codeinsight"

    google_api_key: str = ""
    google_model: str = "gemini-flash-latest"

    frontend_origin: str = "http://localhost:3000"

    jwt_secret_key: str = "dev-secret-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""
    github_oauth_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    frontend_auth_callback_url: str = "http://localhost:3000/auth/callback"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse .env once per process, not once per request.
    return Settings()
