"""
Central application configuration.

All environment-driven settings live here so nothing is hardcoded
inside routes or services. Values are read from a .env file in
local dev, or from real environment variables in production.
"""
from functools import lru_cache
from os import getenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://codeinsight:codeinsight@localhost:5432/codeinsight"

    auth_google_id: str = ""
    google_api_key: str = ""
    google_model: str = "gemini-flash-latest"

    frontend_origin: str = Field(default_factory=lambda: getenv("RENDER_EXTERNAL_URL") or "http://localhost:3000")
    public_site_dir: str = ""

    jwt_secret_key: str = "dev-secret-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""
    github_oauth_redirect_uri: str = Field(
        default_factory=lambda: (getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000") + "/auth/github/callback",
    )
    frontend_auth_callback_url: str = Field(
        default_factory=lambda: (getenv("RENDER_EXTERNAL_URL") or "http://localhost:3000") + "/auth/callback",
    )

    production: bool = False
    signup_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    github_app_id: str = ""
    github_app_private_key_file: str = ""
    github_webhook_secret: str = ""
    github_review_owner_id: str = ""
    github_allowed_installations: str = ""
    github_publish_reviews: bool = False
    pr_ai_enabled: bool = False
    semgrep_binary: str = "semgrep"
    sandbox_docker_host: str = ""
    sandbox_enabled: bool = False
    sandbox_image: str = "codeguard-python-runner:local"
    review_retention_days: int = 30

    @model_validator(mode="after")
    def validate_production(self):
        if self.production and (
            len(self.jwt_secret_key) < 32
            or self.jwt_secret_key == "dev-secret-change-this-in-production"
            or not self.frontend_origin.startswith("https://")
        ):
            raise ValueError("Production requires a unique JWT secret and HTTPS frontend")
        if self.review_retention_days < 1:
            raise ValueError("Review retention must be positive")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse .env once per process, not once per request.
    return Settings()
