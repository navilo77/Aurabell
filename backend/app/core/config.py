"""Application configuration loaded from environment variables.

Uses Pydantic v2 ``BaseSettings`` to read values from ``.env`` (or process
environment variables). Secrets are never logged or printed; the ``__repr__``
override masks any field whose name ends with ``_KEY`` as well as
``DATABASE_URL``.
"""

from __future__ import annotations

from pydantic import Field
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

    # Supabase project credentials (hosted DB + Auth).
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None  # never logged / exposed

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


settings = Settings()