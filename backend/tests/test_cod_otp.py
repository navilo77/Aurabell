"""Tests for Redis-backed COD OTP store."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.redis_otp import CODOTPStore, get_cod_otp_store


class TestCODOTPStore:
    """Test COD OTP store operations."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.eval = AsyncMock(return_value=[1, "OTP verified successfully"])
        redis_mock.close = AsyncMock()
        return redis_mock

    @pytest.fixture
    def otp_store(self, mock_redis):
        """Create CODOTPStore with mocked Redis."""
        with patch("app.core.redis_otp.redis.from_url", return_value=mock_redis):
            store = CODOTPStore(redis_client=mock_redis)
            store._own_redis = False
            return store

    @pytest.mark.asyncio
    async def test_store_otp_creates_key_with_ttl(self, otp_store, mock_redis):
        """Store OTP creates Redis key with correct TTL."""
        await otp_store.store_otp("order-123", "1234")
        
        mock_redis.setex.assert_called_once()
        args, kwargs = mock_redis.setex.call_args
        assert args[0] == "cod_otp:order-123"
        assert args[1] == 300  # 5 minutes TTL
        data = args[2]
        assert "1234" in data  # OTP in stored data
        assert "expires_at" in data
        assert "attempts" in data

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, otp_store, mock_redis):
        """Verify correct OTP returns success and deletes key."""
        # Mock eval to return success
        mock_redis.eval = AsyncMock(return_value=[1, "OTP verified successfully"])
        
        success, message = await otp_store.verify_otp("order-123", "1234")
        
        assert success is True
        assert message == "OTP verified successfully"
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_code(self, otp_store, mock_redis):
        """Verify wrong OTP returns failure with remaining attempts."""
        mock_redis.eval = AsyncMock(return_value=[0, "Invalid OTP. 2 attempts remaining"])
        
        success, message = await otp_store.verify_otp("order-123", "wrong")
        
        assert success is False
        assert "Invalid OTP" in message
        assert "2 attempts remaining" in message

    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, otp_store, mock_redis):
        """Verify expired OTP returns failure."""
        mock_redis.eval = AsyncMock(return_value=[0, "OTP has expired"])
        
        success, message = await otp_store.verify_otp("order-123", "1234")
        
        assert success is False
        assert message == "OTP has expired"

    @pytest.mark.asyncio
    async def test_verify_otp_max_attempts(self, otp_store, mock_redis):
        """Verify max attempts exceeded returns failure."""
        mock_redis.eval = AsyncMock(return_value=[0, "Maximum OTP attempts exceeded"])
        
        success, message = await otp_store.verify_otp("order-123", "1234")
        
        assert success is False
        assert message == "Maximum OTP attempts exceeded"

    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self, otp_store, mock_redis):
        """Verify non-existent OTP returns failure."""
        mock_redis.eval = AsyncMock(return_value=[0, "OTP not found or expired"])
        
        success, message = await otp_store.verify_otp("order-123", "1234")
        
        assert success is False
        assert message == "OTP not found or expired"

    @pytest.mark.asyncio
    async def test_verify_otp_reuse_after_success_fails(self, otp_store, mock_redis):
        """Verify OTP cannot be reused after successful verification."""
        # First verification succeeds
        mock_redis.eval = AsyncMock(return_value=[1, "OTP verified successfully"])
        
        success1, message1 = await otp_store.verify_otp("order-123", "1234")
        assert success1 is True
        
        # Second verification fails because key was deleted
        mock_redis.eval = AsyncMock(return_value=[0, "OTP not found or expired"])
        
        success2, message2 = await otp_store.verify_otp("order-123", "1234")
        assert success2 is False
        assert message2 == "OTP not found or expired"

    @patch("app.core.redis_otp.redis.from_url")
    @pytest.mark.asyncio
    async def test_close_closes_connection(self, mock_from_url):
        """Close method closes Redis connection when we own it."""
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        store = CODOTPStore()
        store._own_redis = True
        store._redis = mock_redis
        
        await store.close()
        mock_redis.close.assert_called_once()


class TestCODOTPStoreIntegration:
    """Integration tests for COD OTP store (requires Redis)."""

    @pytest.mark.asyncio
    async def test_real_redis_operations(self):
        """Test with real Redis if available."""
        import os
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not configured")
        
        store = CODOTPStore()
        try:
            # Store OTP
            await store.store_otp("test-order-1", "5678")
            
            # Verify correct OTP
            success, message = await store.verify_otp("test-order-1", "5678")
            assert success is True
            assert message == "OTP verified successfully"
            
            # Verify wrong OTP fails
            success, message = await store.verify_otp("test-order-1", "0000")
            assert success is False
            assert "Invalid OTP" in message or "OTP not found" in message
        finally:
            await store.close()

    @pytest.mark.asyncio
    async def test_get_cod_otp_store_singleton(self):
        """get_cod_otp_store returns singleton instance."""
        import os
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not configured")
        
        store1 = await get_cod_otp_store()
        store2 = await get_cod_otp_store()
        assert store1 is store2
        await store1.close()