import logging

from sqlalchemy.orm import Session

from app.repositories.sales_repository import SalesRepository

logger = logging.getLogger(__name__)


class SalesService:
    """Service layer for business-oriented sales operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.repository = SalesRepository(db)

    def get_summary(self) -> dict:
        """Fetch aggregated sales summary for the dashboard.
        
        Returns:
            Dictionary with total_revenue, total_orders, average_order_value, top_region
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            logger.info("Fetching sales summary")
            return self.repository.get_sales_summary()
        except Exception as e:
            logger.error(f"Service error fetching sales summary: {e}")
            raise

    def get_monthly_sales(self) -> list[dict]:
        """Fetch monthly sales trend data.
        
        Returns:
            List of monthly sales dictionaries
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            logger.info("Fetching monthly sales")
            return self.repository.get_monthly_sales()
        except Exception as e:
            logger.error(f"Service error fetching monthly sales: {e}")
            raise
