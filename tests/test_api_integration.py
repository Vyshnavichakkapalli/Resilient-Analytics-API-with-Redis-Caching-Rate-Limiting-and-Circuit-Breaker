from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from src.services.circuit_breaker import CircuitBreakerOpenError

client = TestClient(app)

def test_create_metric():
    # Mock rate limiter to always allow
    with patch('src.api.metrics.rate_limiter.is_allowed', return_value=(True, 0)):
        response = client.post("/api/metrics", json={
            "timestamp": "2023-10-27T10:00:00.000Z",
            "value": 100.0,
            "type": "cpu"
        })
        assert response.status_code == 201
        assert response.json() == {"message": "Metric received"}

def test_rate_limiting():
    # Mock rate limiter to deny
    with patch('src.api.metrics.rate_limiter.is_allowed', return_value=(False, 10)):
        response = client.post("/api/metrics", json={
            "timestamp": "2023-10-27T10:00:00.000Z",
            "value": 100.0,
            "type": "cpu"
        })
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "10"

def test_get_summary():
    # Mock redis get to return None (cache miss) then set
    with patch('src.api.metrics.redis_service.get', return_value=None), \
         patch('src.api.metrics.redis_service.set') as mock_set:
        
        response = client.get("/api/metrics/summary?type=cpu")
        assert response.status_code == 200
        assert "average_value" in response.json()
        mock_set.assert_called()

def test_circuit_breaker_endpoint_success():
    with patch('src.api.metrics.circuit_breaker.call', new_callable=AsyncMock) as mock_cb:
        mock_cb.return_value = {"data": "success"}
        response = client.get("/api/external-data")
        assert response.status_code == 200
        assert response.json() == {"data": "success"}

def test_circuit_breaker_endpoint_open():
    with patch('src.api.metrics.circuit_breaker.call', new_callable=AsyncMock) as mock_cb:
        mock_cb.side_effect = CircuitBreakerOpenError("Circuit Open")
        response = client.get("/api/external-data")
        assert response.status_code == 503
        assert response.json()["detail"] == "Service Unavailable (Circuit Open)"
