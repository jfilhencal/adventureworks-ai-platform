from pydantic import BaseModel, Field


class SalesSummary(BaseModel):
    """Sales summary metrics from FactInternetSales."""

    total_revenue: float = Field(..., description="Aggregated revenue amount")
    total_orders: int = Field(..., description="Aggregated order count")
    average_order_value: float = Field(..., description="Average order value")
    top_region: str = Field(..., description="Top sales region by revenue")


class MonthlySalesPoint(BaseModel):
    """Monthly sales data point for trend analysis."""

    month: str = Field(..., description="Month identifier in YYYY-MM format")
    revenue: int = Field(..., description="Revenue for the month")
    orders: int = Field(..., description="Order count for the month")