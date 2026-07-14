from fastapi import APIRouter

from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("")
async def get_forecast() -> dict:
    """Return a mock forecast payload for the forecasting page."""
    service = ForecastService()
    return await service.get_forecast()
