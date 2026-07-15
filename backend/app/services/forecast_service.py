import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

FORECAST_HORIZON_MONTHS = 6
CONFIDENCE_INTERVAL = 0.95
MIN_MONTHS_FOR_FORECAST = 6
MIN_MONTHS_FOR_SEASONALITY = 24


class ForecastService:
    """Forecasts future monthly revenue using Holt-Winters exponential smoothing
    on historical AdventureWorksDW sales data."""

    def __init__(self, db: Session | None = None) -> None:
        """Initialize with an optional database session.

        Args:
            db: SQLAlchemy session used to fetch historical sales. If omitted,
                a mock forecast is returned instead.
        """
        self.db = db

    async def get_forecast(self) -> dict:
        """Return a forecast payload based on historical monthly sales.

        Falls back to a mock payload if no database session is available or
        there isn't enough historical data to fit a model.
        """
        if self.db is None:
            logger.warning("No database session available; returning mock forecast")
            return self._mock_forecast()

        from app.repositories.sales_repository import SalesRepository

        monthly_sales = SalesRepository(self.db).get_monthly_sales()
        if len(monthly_sales) < MIN_MONTHS_FOR_FORECAST:
            logger.warning(
                f"Not enough historical data ({len(monthly_sales)} months) for forecasting; "
                "returning mock forecast"
            )
            return self._mock_forecast()

        try:
            return self._forecast_from_history(monthly_sales)
        except Exception as e:
            logger.error(f"Forecasting failed: {e}", exc_info=True)
            return self._mock_forecast()

    def _forecast_from_history(self, monthly_sales: list[dict[str, Any]]) -> dict:
        """Fit a Holt-Winters exponential smoothing model and forecast future revenue."""
        from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing

        series = pd.Series(
            [row["revenue"] for row in monthly_sales],
            index=pd.PeriodIndex([row["month"] for row in monthly_sales], freq="M"),
        ).astype(float)

        use_seasonal = len(series) >= MIN_MONTHS_FOR_SEASONALITY
        model = ExponentialSmoothing(
            series,
            trend=True,
            seasonal=12 if use_seasonal else None,
            initialization_method="estimated",
        )
        fitted = model.fit()

        prediction = fitted.get_prediction(
            start=len(series), end=len(series) + FORECAST_HORIZON_MONTHS - 1
        )
        mean = prediction.predicted_mean
        ci = prediction.conf_int(alpha=1 - CONFIDENCE_INTERVAL)
        future_index = pd.period_range(series.index[-1] + 1, periods=FORECAST_HORIZON_MONTHS, freq="M")

        result_series = [
            {
                "month": str(period),
                "forecast": round(float(value), 2),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2),
            }
            for period, value, (lower, upper) in zip(future_index, mean, ci.itertuples(index=False))
        ]

        logger.info(
            f"Forecast generated: {FORECAST_HORIZON_MONTHS} months, seasonal={use_seasonal}, "
            f"based on {len(series)} months of history"
        )

        return {
            "forecast_horizon_months": FORECAST_HORIZON_MONTHS,
            "confidence_interval": CONFIDENCE_INTERVAL,
            "series": result_series,
            "note": (
                "Holt-Winters exponential smoothing forecast based on "
                f"{len(series)} months of historical AdventureWorksDW sales."
            ),
        }

    @staticmethod
    def _mock_forecast() -> dict:
        """Return a mock forecast payload when real forecasting isn't possible."""
        return {
            "forecast_horizon_months": FORECAST_HORIZON_MONTHS,
            "confidence_interval": CONFIDENCE_INTERVAL,
            "series": [
                {"month": "2025-07", "forecast": 190000},
                {"month": "2025-08", "forecast": 195000},
                {"month": "2025-09", "forecast": 202000},
            ],
            "note": "Mock forecast: connect a database session with sufficient sales history to enable real forecasting.",
        }
