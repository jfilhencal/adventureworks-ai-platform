from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("")
async def get_forecast(db: Session = Depends(get_db)) -> dict:
    """Return a forecast payload based on historical AdventureWorksDW sales data."""
    service = ForecastService(db)
    return await service.get_forecast()
