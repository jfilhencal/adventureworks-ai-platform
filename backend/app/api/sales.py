import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sales import MonthlySalesPoint, SalesSummary
from app.services.sales_service import SalesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["sales"])


def get_sales_service(db: Session = Depends(get_db)) -> SalesService:
    """Dependency provider for the sales service with database session.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        SalesService instance
    """
    return SalesService(db)


@router.get("/summary", response_model=SalesSummary)
async def get_sales_summary(service: SalesService = Depends(get_sales_service)) -> SalesSummary:
    """Return an aggregated sales summary from FactInternetSales.
    
    Returns:
        SalesSummary with total_revenue, total_orders, average_order_value, top_region
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        summary = service.get_summary()
        logger.info(f"Summary returned from service: {summary}")
        print(summary)
        return SalesSummary(**summary)
    except Exception as e:
        logger.error(f"Failed to retrieve sales summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sales summary",
        )


@router.get("/monthly", response_model=list[MonthlySalesPoint])
async def get_monthly_sales(service: SalesService = Depends(get_sales_service)) -> list[MonthlySalesPoint]:
    """Return monthly sales data for charts and trend analysis.
    
    Returns:
        List of MonthlySalesPoint with month, revenue, and orders
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        monthly = service.get_monthly_sales()
        return [MonthlySalesPoint(**item) for item in monthly]
    except Exception as e:
        logger.error(f"Failed to retrieve monthly sales: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monthly sales",
        )
