"""Application configuration loaded from environment variables.

Uses Pydantic v2 ``BaseSettings`` to read values from ``.env`` (or process
environment variables). Secrets are never logged or printed; the ``__repr__``
override masks any field whose name ends with ``_KEY`` as well as
``DATABASE_URL``.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Aura Bell API.

    All fields can be supplied through a ``.env`` file or the process
    environment. Unknown keys are ignored (``extra="ignore"``) so existing
    environment variables do not break startup.
    """

    APP_NAME: str = "Aura Bell API"
    APP_ENV: str = "development"

    # PostgreSQL async connection URL (asyncpg driver).
    DATABASE_URL: str = ""

    # Database connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Supabase project credentials (hosted DB + Auth).
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None  # never logged / exposed

    # Redis configuration
    REDIS_URL: str | None = None
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_SOCKET_CONNECT_TIMEOUT: float = 5.0

    # Rate limiting configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    RATE_LIMIT_PAYMENT_PER_MINUTE: int = 5
    RATE_LIMIT_COMMUNITY_PER_MINUTE: int = 30
    RATE_LIMIT_ADMIN_PER_MINUTE: int = 100

    # External API timeouts
    HTTP_TIMEOUT_CONNECT: float = 5.0
    HTTP_TIMEOUT_READ: float = 30.0
    HTTP_TIMEOUT_TOTAL: float = 60.0

    # AmarPay configuration
    AMARPAY_STORE_ID: str | None = None
    AMARPAY_SIGNATURE_KEY: str | None = None
    AMARPAY_BASE_URL: str = "https://sandbox.aamarpay.com"
    AMARPAY_ENVIRONMENT: str = "sandbox"

    # CORS configuration
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ALLOW_CREDENTIALS: bool = True

    # Trusted hosts
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,*.localhost,testserver"

    # Application base URL
    APP_BASE_URL: str = "http://localhost:8000"

    # Security
    SESSION_SECRET_KEY: str | None = None
    SESSION_COOKIE_SECURE: bool = False
    # SameSite must stay "lax" in production — "strict" breaks AmarPay
    # payment redirects (cross-site top-level navigation).
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_COOKIE_DOMAIN: str | None = None
    SESSION_COOKIE_MAX_AGE: int = 604800

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def _mask(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "***"
        return value[:4] + "..." + value[-4:]

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        masked: dict[str, str] = {}
        for name in self.model_fields:
            value = getattr(self, name)
            if name == "DATABASE_URL" or name.endswith("_KEY"):
                masked[name] = self._mask(value) if value else ""
            else:
                masked[name] = repr(value)
        return f"Settings({masked})"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS_ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        """Parse TRUSTED_HOSTS into a list."""
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    def validate_production_config(self) -> None:
        """Validate required settings for production environment.
        
        Raises:
            ValueError: If required production settings are missing.
        """
        if self.APP_ENV != "production":
            return

        required_production = {
            "DATABASE_URL": self.DATABASE_URL,
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_ANON_KEY": self.SUPABASE_ANON_KEY,
            "SUPABASE_SERVICE_ROLE_KEY": self.SUPABASE_SERVICE_ROLE_KEY,
            "SESSION_SECRET_KEY": self.SESSION_SECRET_KEY,
            "REDIS_URL": self.REDIS_URL,
            "AMARPAY_STORE_ID": self.AMARPAY_STORE_ID,
            "AMARPAY_SIGNATURE_KEY": self.AMARPAY_SIGNATURE_KEY,
        }

        missing = [key for key, value in required_production.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required production configuration: {', '.join(missing)}. "
                "Set these environment variables or check your .env file."
            )

        # Validate cookie security
        if not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SECURE must be True in production")

        # Validate CORS is not wildcard
        if "*" in self.cors_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must not contain '*' in production")

        # Validate trusted hosts
        if "localhost" in self.trusted_hosts_list or "127.0.0.1" in self.trusted_hosts_list:
            raise ValueError("TRUSTED_HOSTS must not contain localhost in production")


settings = Settings()

# Validate production config on import (fail fast)
try:
    settings.validate_production_config()
except ValueError as e:
    if settings.APP_ENV == "production":
        raise
    # In development, just warn
    import logging
    logging.getLogger(__name__).warning(f"Production config validation skipped: {e}")