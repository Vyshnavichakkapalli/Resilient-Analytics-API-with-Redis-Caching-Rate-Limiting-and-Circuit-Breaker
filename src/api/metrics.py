from datetime import datetime
from typing import List, Optional
import json
from fastapi import APIRouter, HTTPException, status, Request
from src.services.storage import add_metric, get_all_metrics
from src.services.redis_service import redis_service
from src.services.rate_limiter import rate_limiter

router = APIRouter()

class MetricInput(BaseModel):
    timestamp: datetime
    value: float
    type: str

class MetricSummary(BaseModel):
    type: str
    period: str
    average_value: float
    count: int

@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def create_metric(metric: MetricInput, request: Request):
    client_ip = request.client.host
    is_allowed, retry_after = rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests",
            headers={"Retry-After": str(retry_after)}
        )

    add_metric(metric.dict())
    return {"message": "Metric received"}

@router.get("/metrics/summary", response_model=MetricSummary)
async def get_metrics_summary(type: str, period: str = "daily"):
    # Cache key based on type and period
    cache_key = f"summary:{type}:{period}"
    
    # Try to get from cache
    cached_data = redis_service.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # Basic implementation: filter in-memory list
    all_metrics = get_all_metrics()
    filtered_metrics = [
        m for m in all_metrics 
        if m['type'] == type
        # In a real app, we'd filter by 'period' (timestamp) too
    ]

    if not filtered_metrics:
        # Return empty summary (not cached to avoid caching empty results if data is delayed, 
        # or cache with short TTL if frequent empty queries are a problem)
        return MetricSummary(type=type, period=period, average_value=0.0, count=0)

    total_value = sum(m['value'] for m in filtered_metrics)
    count = len(filtered_metrics)
    average = total_value / count

    summary = MetricSummary(
        type=type,
        period=period,
        average_value=average,
        count=count
    )

    # Cache the result
    redis_service.set(cache_key, summary.dict(), ttl=60) # Cache for 60 seconds

    return summary

from src.services.external_service import fetch_risky_external_data
from src.services.circuit_breaker import circuit_breaker, CircuitBreakerOpenError

@router.get("/external-data")
async def get_external_data():
    try:
        data = await circuit_breaker.call(fetch_risky_external_data)
        return data
    except CircuitBreakerOpenError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable (Circuit Open)"
        )
    except RuntimeError as e:
         raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
