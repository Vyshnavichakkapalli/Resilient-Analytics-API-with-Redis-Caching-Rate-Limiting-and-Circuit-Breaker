import pytest
from unittest.mock import MagicMock, patch
from src.services.rate_limiter import RateLimiter

def test_rate_limiter_allows_request():
    with patch('src.services.rate_limiter.redis_service') as mock_redis:
        limiter = RateLimiter(limit=5, window=60)
        
        # Mock INCR to return 1 (first request)
        mock_redis.incr.return_value = 1
        
        allowed, retry_after = limiter.is_allowed("127.0.0.1")
        
        assert allowed is True
        assert retry_after == 0
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once() # Should expire on first request

def test_rate_limiter_blocks_request():
    with patch('src.services.rate_limiter.redis_service') as mock_redis:
        limiter = RateLimiter(limit=5, window=60)
        
        # Mock INCR to return 6 (limit exceeded)
        mock_redis.incr.return_value = 6
        mock_redis.ttl.return_value = 30
        
        allowed, retry_after = limiter.is_allowed("127.0.0.1")
        
        assert allowed is False
        assert retry_after == 30
