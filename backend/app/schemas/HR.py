from pydantic import BaseModel, Field


class HRSummary(BaseModel):
    """Aggregated HR metrics."""

    total_employees: int = Field(..., description="Total number of employees")
    average_tenure: float = Field(..., description="Average tenure of employees")
    department_distribution: dict[str, int] = Field(
        ...,
        description="Employee count per department",
    )


class MonthlyHRDataPoint(BaseModel):
    """Monthly HR data point for trend analysis."""

    month: str = Field(..., description="Month identifier in YYYY-MM format")
    new_hires: int = Field(..., description="Number of new hires for the month")
    terminations: int = Field(..., description="Number of terminations for the month")
    net_change: int = Field(..., description="Net change in headcount for the month")
    cumulative_headcount: int = Field(
        ...,
        description="Cumulative headcount at the end of the month",
    )