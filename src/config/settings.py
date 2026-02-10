from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Resilient Analytics API"
    redis_host: str = "localhost"
    redis_port: int = 6379
    external_service_failure_rate: float = 0.1
    # feature flags or other configs can go here

    class Config:
        env_file = ".env"

settings = Settings()
