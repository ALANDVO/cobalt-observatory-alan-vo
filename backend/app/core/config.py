"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Cobalt Observatory"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./cobalt.db"

    # Security
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # LLM (optional)
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # Keycloak/OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "cobalt"
    keycloak_client_id: str = "cobalt-observatory"
    keycloak_client_secret: str = ""

    # Observability
    otel_endpoint: str = ""
    otel_service_name: str = "cobalt-observatory"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()