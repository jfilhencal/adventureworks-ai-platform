import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SalesRepository:
    """Repository responsible for retrieving sales data from AdventureWorksDW."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_sales_summary(self) -> dict[str, Any]:
        """Query FactInternetSales for revenue, order count, and average order value.
        
        Returns:
            Dictionary with total_revenue, total_orders, average_order_value
            
        Raises:
            Exception: If database query fails
        """
        try:
            query = text("""
                SELECT 
                    SUM(f.SalesAmount) AS total_revenue,
                    COUNT_BIG(*) AS total_orders,
                    AVG(f.SalesAmount) AS average_order_value,
                    ISNULL((
                        SELECT TOP 1 d.SalesTerritoryRegion
                        FROM dbo.FactInternetSales AS f2
                        JOIN dbo.DimSalesTerritory AS d
                            ON f2.SalesTerritoryKey = d.SalesTerritoryKey
                        GROUP BY d.SalesTerritoryRegion
                        ORDER BY SUM(f2.SalesAmount) DESC
                    ), 'N/A') AS top_region
                FROM dbo.FactInternetSales AS f
            """)
            
            result = self.db.execute(query).fetchone()
            
            if result is None:
                logger.warning("No sales data found in FactInternetSales")
                return {
                    "total_revenue": 0,
                    "total_orders": 0,
                    "average_order_value": 0,
                    "top_region": "N/A",
                }
            
            total_revenue = float(result[0]) if result[0] else 0
            total_orders = int(result[1]) if result[1] else 0
            average_order_value = float(result[2]) if result[2] else 0
            top_region = result[3] if result[3] else "N/A"
            
            logger.info(
                f"Sales summary retrieved: ${total_revenue:,.2f} revenue, "
                f"{total_orders:,} orders, top region {top_region}"
            )
            
            return {
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "average_order_value": average_order_value,
                "top_region": top_region,
            }
        except Exception as e:
            logger.error(f"Error retrieving sales summary: {e}", exc_info=True)
            raise

    def get_monthly_sales(self) -> list[dict[str, Any]]:
        """Query FactInternetSales for monthly revenue and order trends.
        
        Returns:
            List of dictionaries with month, revenue, and order_count
            
        Raises:
            Exception: If database query fails
        """
        try:
            query = text("""
                SELECT 
                    CONVERT(VARCHAR(7), OrderDate, 120) AS month_key,
                    SUM(SalesAmount) AS revenue,
                    COUNT_BIG(*) AS order_count
                FROM dbo.FactInternetSales
                GROUP BY CONVERT(VARCHAR(7), OrderDate, 120)
                ORDER BY month_key
            """)
            
            results = self.db.execute(query).fetchall()
            
            monthly_data = [
                {
                    "month": row[0],
                    "revenue": int(row[1]) if row[1] else 0,
                    "orders": int(row[2]) if row[2] else 0,
                }
                for row in results
            ]
            
            logger.info(f"Monthly sales data retrieved: {len(monthly_data)} months")
            return monthly_data
        except Exception as e:
            logger.error(f"Error retrieving monthly sales: {e}", exc_info=True)
            raise
