"""Tests for configuration validation."""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch

from app.core.config import Settings, settings


class TestSettings:
    """Test configuration settings."""

    def test_default_values(self):
        """Test default values are set correctly."""
        s = Settings()
        assert s.APP_NAME == "Aura Bell API"
        assert s.APP_ENV == "development"
        assert s.DB_POOL_SIZE == 10
        assert s.SESSION_COOKIE_SAMESITE == "lax"

    def test_cors_origins_parsing(self):
        """Test CORS origins are parsed correctly."""
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "http://a.com, http://b.com"}):
            s = Settings()
            assert s.cors_origins == ["http://a.com", "http://b.com"]

    def test_cors_origins_empty(self):
        """Test empty CORS origins returns empty list."""
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": ""}):
            s = Settings()
            assert s.cors_origins == []

    def test_trusted_hosts_parsing(self):
        """Test trusted hosts are parsed correctly."""
        with patch.dict(os.environ, {"TRUSTED_HOSTS": "a.com, b.com"}):
            s = Settings()
            assert s.trusted_hosts_list == ["a.com", "b.com"]

    def test_mask_method(self):
        """Test value masking for secrets."""
        s = Settings()
        assert s._mask("") == ""
        assert s._mask("short") == "***"
        assert s._mask("12345678") == "***"
        assert s._mask("123456789012") == "1234...9012"

    def test_repr_masks_secrets(self):
        """Test __repr__ masks sensitive fields."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SECRET_KEY": "secret-value",
            "API_KEY": "api-key-value",
        }):
            s = Settings()
            repr_str = repr(s)
            assert "secret-value" not in repr_str
            assert "api-key-value" not in repr_str
            assert "***" in repr_str or "..." in repr_str


class TestProductionConfigValidation:
    """Test production configuration validation."""

    def test_development_env_skips_validation(self):
        """Development environment skips production validation."""
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            s = Settings()
            # Should not raise
            s.validate_production_config()

    def test_production_missing_database_url_raises(self):
        """Production requires DATABASE_URL."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "",
            "SUPABASE_URL": "http://test.com",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "secret",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="DATABASE_URL"):
                s.validate_production_config()

    def test_production_missing_supabase_raises(self):
        """Production requires Supabase credentials."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SUPABASE_URL": "",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "secret",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="SUPABASE_URL"):
                s.validate_production_config()

    def test_production_missing_session_secret_raises(self):
        """Production requires SESSION_SECRET_KEY."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SUPABASE_URL": "http://test.com",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="SESSION_SECRET_KEY"):
                s.validate_production_config()

    def test_production_session_cookie_secure_required(self):
        """Production requires SESSION_COOKIE_SECURE=true."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SUPABASE_URL": "http://test.com",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "secret",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
            "SESSION_COOKIE_SECURE": "false",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="SESSION_COOKIE_SECURE"):
                s.validate_production_config()

    def test_production_cors_wildcard_rejected(self):
        """Production rejects CORS wildcard."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SUPABASE_URL": "http://test.com",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "secret",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
            "SESSION_COOKIE_SECURE": "true",
            "CORS_ALLOWED_ORIGINS": "*",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS"):
                s.validate_production_config()

    def test_production_localhost_in_trusted_hosts_rejected(self):
        """Production rejects localhost in trusted hosts."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "SUPABASE_URL": "http://test.com",
            "SUPABASE_ANON_KEY": "anon",
            "SUPABASE_SERVICE_ROLE_KEY": "service",
            "SESSION_SECRET_KEY": "secret",
            "REDIS_URL": "redis://localhost",
            "AMARPAY_STORE_ID": "store",
            "AMARPAY_SIGNATURE_KEY": "sig",
            "SESSION_COOKIE_SECURE": "true",
            "TRUSTED_HOSTS": "localhost,example.com",
        }):
            s = Settings()
            with pytest.raises(ValueError, match="TRUSTED_HOSTS"):
                s.validate_production_config()


class TestGlobalSettings:
    """Test global settings instance."""

    def test_settings_instance_exists(self):
        """Global settings instance is created."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_are_cached(self):
        """Settings are cached (singleton)."""
        from app.core.config import settings as settings2
        assert settings is settings2