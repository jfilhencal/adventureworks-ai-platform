import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HRRepository:
    """Repository responsible for retrieving HR data from AdventureWorksDW."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_HR_summary(self) -> dict[str, Any]:
        """Query aggregated HR metrics: headcount, average tenure, and department mix.

        Deliberately returns only aggregate statistics (no per-employee rows) so this
        data is safe to hand to the AI assistant or display on a dashboard without
        exposing individual PII (names, birth dates, marital status, compensation).
        """
        try:
            totals_query = text("""
                SELECT
                    COUNT(*) AS total_employees,
                    AVG(CAST(DATEDIFF(YEAR, e.HireDate, GETDATE()) AS FLOAT)) AS average_tenure
                FROM [dbo].[DimEmployee] e
                WHERE e.CurrentFlag = 1
            """)
            department_query = text("""
                SELECT e.DepartmentName, COUNT(*) AS employee_count
                FROM [dbo].[DimEmployee] e
                WHERE e.CurrentFlag = 1
                GROUP BY e.DepartmentName
                ORDER BY employee_count DESC
            """)

            totals = self.db.execute(totals_query).fetchone()
            departments = self.db.execute(department_query).fetchall()

            total_employees = int(totals[0]) if totals and totals[0] else 0
            average_tenure = round(float(totals[1]), 2) if totals and totals[1] else 0.0
            department_distribution = {row[0]: int(row[1]) for row in departments if row[0]}

            logger.info(
                f"HR summary retrieved: {total_employees} employees across "
                f"{len(department_distribution)} departments, avg tenure {average_tenure} years"
            )

            return {
                "total_employees": total_employees,
                "average_tenure": average_tenure,
                "department_distribution": department_distribution,
            }
        except Exception as e:
            logger.error(f"Error retrieving HR summary: {e}", exc_info=True)
            raise

    def get_monthly_HR_data(self) -> list[dict[str, Any]]:
        """Query DimEmployee for monthly HR trends.
        
        Returns:
            List of dictionaries with month, new_hires, and terminations
            
        Raises:
            Exception: If database query fails
        """
        try:
            query = text("""

            WITH MonthlyActivity AS (
                SELECT 
                    YEAR(HireDate) AS Year,
                    MONTH(HireDate) AS MonthNum,
                    COUNT(*) AS NewHires
                FROM [dbo].[DimEmployee]
                WHERE HireDate IS NOT NULL
                GROUP BY YEAR(HireDate), MONTH(HireDate)
            ),
            MonthlyTerminations AS (
                SELECT 
                    YEAR(EndDate) AS Year,
                    MONTH(EndDate) AS MonthNum,
                    COUNT(*) AS Terminations
                FROM [dbo].[DimEmployee]
                WHERE EndDate IS NOT NULL
                GROUP BY YEAR(EndDate), MONTH(EndDate)
            ),
            AllMonths AS (
                SELECT Year, MonthNum FROM MonthlyActivity
                UNION
                SELECT Year, MonthNum FROM MonthlyTerminations
            )
            SELECT 
                FORMAT(DATEFROMPARTS(am.Year, am.MonthNum, 1), 'yyyy-MM') AS Month,
                DATENAME(MONTH, DATEFROMPARTS(am.Year, am.MonthNum, 1)) AS MonthName,
                am.Year,
                ISNULL(ma.NewHires, 0) AS NewHires,
                ISNULL(mt.Terminations, 0) AS Terminations,
                ISNULL(ma.NewHires, 0) - ISNULL(mt.Terminations, 0) AS NetChange,
                SUM(ISNULL(ma.NewHires, 0) - ISNULL(mt.Terminations, 0)) 
                    OVER (ORDER BY am.Year, am.MonthNum 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS CumulativeHeadcount
            FROM AllMonths am
            LEFT JOIN MonthlyActivity ma ON am.Year = ma.Year AND am.MonthNum = ma.MonthNum
            LEFT JOIN MonthlyTerminations mt ON am.Year = mt.Year AND am.MonthNum = mt.MonthNum
            ORDER BY am.Year, am.MonthNum;
            """)
            
            results = self.db.execute(query).fetchall()
            
            monthly_data = [
                {
                    "month": row[0],
                    "month_name": row[1],
                    "year": row[2],
                    "new_hires": int(row[3]) if row[3] else 0,
                    "terminations": int(row[4]) if row[4] else 0,
                    "net_change": int(row[5]) if row[5] else 0,
                    "cumulative_headcount": int(row[6]) if row[6] else 0,
                }
                for row in results
            ]
            
            logger.info(f"Monthly HR data retrieved: {len(monthly_data)} months")
            return monthly_data
        except Exception as e:
            logger.error(f"Error retrieving monthly sales: {e}", exc_info=True)
            raise
