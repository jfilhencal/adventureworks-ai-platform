class ForecastService:
    """Forecasting service placeholder for Prophet or Azure ML integration."""

    async def get_forecast(self) -> dict:
        """Return a mock forecast payload until the forecasting pipeline is wired."""
        return {
            "forecast_horizon_months": 6,
            "confidence_interval": 0.95,
            "series": [
                {"month": "2025-07", "forecast": 190000},
                {"month": "2025-08", "forecast": 195000},
                {"month": "2025-09", "forecast": 202000},
            ],
            "note": "TODO: Replace with Prophet or Azure AI Forecasting implementation.",
        }
