import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.HR import HRSummary, MonthlyHRDataPoint
from app.services.HR_service import HRService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hr", tags=["hr"])


def get_hr_service(db: Session = Depends(get_db)) -> HRService:
    """Dependency provider for the HR service with database session.

    Args:
        db: Database session from dependency injection

    Returns:
        HRService instance
    """
    return HRService(db)


@router.get("/summary", response_model=HRSummary)
async def get_hr_summary(service: HRService = Depends(get_hr_service)) -> HRSummary:
    """Return aggregated HR metrics from DimEmployee.

    Returns:
        HRSummary with total_employees, average_tenure, department_distribution

    Raises:
        HTTPException: If database query fails
    """
    try:
        summary = service.get_HR_summary()
        return HRSummary(**summary)
    except Exception as e:
        logger.error(f"Failed to retrieve HR summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HR summary",
        )


@router.get("/monthly", response_model=list[MonthlyHRDataPoint])
async def get_monthly_hr_data(service: HRService = Depends(get_hr_service)) -> list[MonthlyHRDataPoint]:
    """Return monthly HR trend data for charts and analysis.

    Returns:
        List of MonthlyHRDataPoint with hires, terminations, and headcount trends

    Raises:
        HTTPException: If database query fails
    """
    try:
        monthly = service.get_monthly_HR_data()
        return [MonthlyHRDataPoint(**item) for item in monthly]
    except Exception as e:
        logger.error(f"Failed to retrieve monthly HR data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monthly HR data",
        )
