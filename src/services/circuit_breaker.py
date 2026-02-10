import time
import asyncio
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 10):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = CircuitState.HALF_OPEN
                    # print("Circuit transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError("Circuit is OPEN")
            
            if self.state == CircuitState.HALF_OPEN:
                # In half-open, we allow one request. If it fails, back to open.
                # If it succeeds, back to closed.
                try:
                    result = await func(*args, **kwargs)
                    self._reset()
                    return result
                except Exception as e:
                    self._record_failure()
                    raise e

            # CLOSED state
            try:
                result = await func(*args, **kwargs)
                self._reset() # Success resets the count
                return result
            except Exception as e:
                self._record_failure()
                raise e

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        # print(f"Failure recorded. Count: {self.failure_count}")
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            # print("Circuit transitioning to OPEN")

    def _reset(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        # print("Circuit resetting to CLOSED")

circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=10)
