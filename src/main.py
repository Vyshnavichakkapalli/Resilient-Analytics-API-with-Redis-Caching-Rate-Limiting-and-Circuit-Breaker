from fastapi import FastAPI
from src.api.metrics import router as metrics_router
from src.config.settings import settings

app = FastAPI(title=settings.app_name)

app.include_router(metrics_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
