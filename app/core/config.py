"""Environment-based configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    # Firebase
    firebase_credentials_path: Optional[str] = None
    dev_bypass_token: Optional[str] = None  # non-None enables dev bypass

    # Downstream services
    user_service_url: str = "http://user-service:8002"
    payment_service_url: str = "http://payment-service:8001"

    # Internal secret (shared with downstream)
    internal_api_secret: str = "your-internal-service-secret-change-in-production"

    # Forwarding
    downstream_timeout: float = 10.0

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
