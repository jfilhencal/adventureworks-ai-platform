import logging

from fastapi import FastAPI

from app.api import ai, forecast, health, sales
from app.core.config import get_settings
from app.core.database import verify_connection
from app.core.logging_config import configure_logging

# Configure logging at startup
configure_logging(level="INFO")
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production-style AI analytics platform with AdventureWorksDW integration.",
)

app.include_router(health.router)
app.include_router(sales.router)
app.include_router(forecast.router)
app.include_router(ai.router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application resources and verify database connectivity."""
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    if not verify_connection():
        logger.warning("Database connection verification failed; some endpoints may not work")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("Application shutdown")


@app.get("/")
async def root() -> dict:
    """Root endpoint for service discovery."""
    logger.info("Root endpoint accessed")
    return {
        "message": "AdventureWorks AI Platform API",
        "status": "ready",
        "environment": settings.environment,
    }
