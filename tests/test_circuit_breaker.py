import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.services.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenError

@pytest.mark.asyncio
async def test_circuit_breaker_initial_state():
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=1)
    mock_func = AsyncMock(side_effect=Exception("Failure"))

    # First failure
    with pytest.raises(Exception):
        await cb.call(mock_func)
    assert cb.failure_count == 1
    assert cb.state == CircuitState.CLOSED

    # Second failure - should open
    with pytest.raises(Exception):
        await cb.call(mock_func)
    assert cb.failure_count == 2
    assert cb.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=10)
    cb.state = CircuitState.OPEN
    cb.last_failure_time = asyncio.get_event_loop().time() # Mock time if needed, but here we just rely on time logic
    
    # Needs to rely on time.time(), so let's patch it
    with patch('time.time', return_value=100):
        cb.last_failure_time = 100
        
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(AsyncMock())

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_logic():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=5)
    
    # Move to OPEN
    cb.state = CircuitState.OPEN
    cb.last_failure_time = 100

    # Simulate time passed > reset_timeout
    with patch('time.time', return_value=106):
        # First call should transition to HALF_OPEN and be allowed
        mock_success = AsyncMock(return_value="Success")
        result = await cb.call(mock_success)
        
        assert result == "Success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=5)
    
    # Move to OPEN
    cb.state = CircuitState.OPEN
    cb.last_failure_time = 100

    # Simulate time passed > reset_timeout
    with patch('time.time', return_value=106):
        # Call fails
        mock_failure = AsyncMock(side_effect=Exception("Failed"))
        with pytest.raises(Exception):
            await cb.call(mock_failure)
        
        assert cb.state == CircuitState.OPEN
