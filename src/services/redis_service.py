import redis
import json
from typing import Optional, Any
from src.config.settings import settings

class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[str]:
        return self.redis_client.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.redis_client.setex(key, ttl, value)

    def ping(self) -> bool:
        try:
            return self.redis_client.ping()
        except redis.ConnectionError:
            return False

    # For rate limiting
    def incr(self, key: str) -> int:
        return self.redis_client.incr(key)
    
    def expire(self, key: str, ttl: int):
        self.redis_client.expire(key, ttl)

    def ttl(self, key: str) -> int:
        return self.redis_client.ttl(key)

redis_service = RedisService()
