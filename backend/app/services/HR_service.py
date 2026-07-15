import logging

from sqlalchemy.orm import Session

from app.repositories.HR_repository import HRRepository

logger = logging.getLogger(__name__)


class HRService:
    """Service layer for business-oriented HR operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.repository = HRRepository(db)

    def get_HR_summary(self) -> dict:
        """Fetch aggregated HR summary for the dashboard.
        
        Returns:
            Dictionary with total_employees, average_tenure, department_distribution
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            logger.info("Fetching HR summary")
            return self.repository.get_HR_summary()
        except Exception as e:
            logger.error(f"Service error fetching HR summary: {e}")
            raise

    def get_monthly_HR_data(self) -> list[dict]:
        """Fetch monthly HR trend data.

        Returns:
            List of monthly HR dictionaries
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            logger.info("Fetching monthly HR data")
            return self.repository.get_monthly_HR_data()
        except Exception as e:
            logger.error(f"Service error fetching monthly HR data: {e}")
            raise
