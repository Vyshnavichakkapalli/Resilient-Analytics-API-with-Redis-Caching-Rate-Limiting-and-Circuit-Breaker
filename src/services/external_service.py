import random
import asyncio
from src.config.settings import settings

async def fetch_risky_external_data():
    """
    Simulates fetching data from an external service.
    Fails randomly based on EXTERNAL_SERVICE_FAILURE_RATE.
    """
    # Simulate network latency
    await asyncio.sleep(0.1)

    if random.random() < settings.external_service_failure_rate:
        raise RuntimeError("Simulated external service failure")
    
    return {"data": "success", "value": random.randint(1, 100)}
