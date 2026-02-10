from fastapi import HTTPException, status
from src.services.redis_service import redis_service
import time

class RateLimiter:
    def __init__(self, limit: int = 5, window: int = 60):
        self.limit = limit
        self.window = window

    def is_allowed(self, client_id: str) -> tuple[bool, int]:
        """
        Checks if the request is allowed for the given client_id.
        Returns (is_allowed, retry_after).
        Using Fixed Window Counters.
        """
        # Create a window key based on the current timestamp (e.g., limit per minute)
        current_window = int(time.time() // self.window)
        key = f"rate_limit:{client_id}:{current_window}"

        # Increment the counter
        request_count = redis_service.incr(key)

        # Set expiration if it's the first request in the window
        if request_count == 1:
            redis_service.expire(key, self.window)

        if request_count > self.limit:
            # Calculate retry after (time remaining in the current window)
            # This is an approximation. A more precise one would use TTL.
            ttl = redis_service.ttl(key)
            retry_after = ttl if ttl > 0 else self.window
            return False, retry_after
        
        return True, 0

# Global rate limiter instance (can be configured via settings later)
# Default: 5 requests per 60 seconds (1 minute)
rate_limiter = RateLimiter(limit=5, window=60)
