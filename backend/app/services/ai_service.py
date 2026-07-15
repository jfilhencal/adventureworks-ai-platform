import json
import logging
import re
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings

logger = logging.getLogger(__name__)


# Tool schemas exposed to the model so it can pull real AdventureWorks data instead of
# guessing. 
_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": (
                "Get aggregated AdventureWorks sales metrics: total revenue, total orders, "
                "average order value, and the top-performing sales region."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_sales",
            "description": "Get AdventureWorks revenue and order count broken down by month.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Get the sales revenue forecast for upcoming months.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # Add HR summary capabilities
        { 
        "type": "function",
        "function": {
            "name": "get_HR_summary",
            "description": "Get aggregated HR metrics: total employees, average tenure, and department distribution.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    { 
        "type": "function",
        "function": {
            "name": "get_monthly_HR_data",
            "description": "Get monthly HR data: new hires, terminations, net change, and cumulative headcount.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
   ]


@lru_cache
def _get_credential():
    """
    Return a cached azure-identity credential based on AZURE_OPENAI_AUTH_MODE.
    """

    from azure.identity import (
        DefaultAzureCredential,
        InteractiveBrowserCredential,
    )

    settings = get_settings()

    logger.info(
        "Creating Azure credential (auth_mode=%s)",
        settings.azure_openai_auth_mode,
    )

    if settings.azure_openai_auth_mode == "interactive":
        kwargs: dict[str, str] = {}

        if settings.azure_tenant_id:
            kwargs["tenant_id"] = settings.azure_tenant_id

        if settings.sql_user:
            kwargs["login_hint"] = settings.sql_user

        logger.warning(
            "Using InteractiveBrowserCredential. "
            "This may trigger browser login prompts."
        )

        return InteractiveBrowserCredential(**kwargs)

    logger.info("Using DefaultAzureCredential")

    return DefaultAzureCredential(
        managed_identity_client_id=
            settings.azure_openai_managed_identity_client_id or None
    )


@lru_cache
def _get_openai_client():
    """
    Build an AzureOpenAI client authenticated via Microsoft Entra ID.
    """

    from azure.identity import get_bearer_token_provider
    from openai import AzureOpenAI

    settings = get_settings()

    logger.info("Creating Azure OpenAI client")

    token_provider = get_bearer_token_provider(
        _get_credential(),
        "https://cognitiveservices.azure.com/.default",
    )

    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.azure_openai_api_version,
        timeout=60,
    )



class AIService:
    """Generative AI service backed by Azure AI Foundry / Azure OpenAI.

    Grounds the model in real AdventureWorks data via tool/function calling: the model can
    call get_sales_summary/get_monthly_sales/get_forecast/get_HR_summary/get_monthly_HR_data,
    which are backed by the same Sales/Forecast/HR services used by the REST endpoints,
    instead of inventing numbers. HR tools only expose aggregate statistics, never
    per-employee PII.
    """

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    async def _call_tool(self, name: str) -> dict:
        """Execute a tool call by name against the real service layer."""
        from app.services.forecast_service import ForecastService
        from app.services.HR_service import HRService
        from app.services.sales_service import SalesService

        if name in ("get_sales_summary", "get_monthly_sales"):
            if self.db is None:
                return {"error": "No database session available"}
            service = SalesService(self.db)
            if name == "get_sales_summary":
                return service.get_summary()
            return {"months": service.get_monthly_sales()}
        if name == "get_forecast":
            return await ForecastService(self.db).get_forecast()
        if name in ("get_HR_summary", "get_monthly_HR_data"):
            if self.db is None:
                return {"error": "No database session available"}
            hr_service = HRService(self.db)
            if name == "get_HR_summary":
                return hr_service.get_HR_summary()
            return {"months": hr_service.get_monthly_HR_data()}
        return {"error": f"Unknown tool: {name}"}

    async def analyze(self, prompt: str) -> dict:
        """Return an AI-generated analysis, falling back to a mock payload when Foundry isn't configured."""
        settings = get_settings()
        if not settings.azure_openai_endpoint or not settings.azure_openai_deployment:
            logger.warning("Azure OpenAI endpoint/deployment not configured; returning mock AI response")
            return self._mock_response(prompt)

        try:
            client = _get_openai_client()
            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                        "You are a business analyst assistant for the AdventureWorks AI Platform. "
                        "Use the provided tools to fetch real sales/forecast/HR data before answering "
                        "questions about revenue, orders, regions, trends, headcount, hiring, or turnover. "
                        "For HR questions, only report aggregate statistics (headcounts, distributions, "
                        "averages) - never individual employee personal details. Provide concise, "
                        "actionable insights based on the user's request."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=messages,
                tools=_TOOLS,
                max_completion_tokens=500,
            )
            message = response.choices[0].message

            # Resolve any tool calls the model requested, then ask it for a final answer
            # grounded in the tool results.
            if message.tool_calls:
                messages.append(message.model_dump(exclude_none=True))
                for tool_call in message.tool_calls:
                    result = await self._call_tool(tool_call.function.name)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, default=str),
                        }
                    )
                response = client.chat.completions.create(
                    model=settings.azure_openai_deployment,
                    messages=messages,
                    max_completion_tokens=500,
                )
                message = response.choices[0].message

            summary = message.content or ""
            return {"prompt": prompt, "summary": summary, "suggestions": []}
        except Exception as e:
            logger.error(f"Azure OpenAI request failed: {e}")
            raise

    @staticmethod
    def _mock_response(prompt: str) -> dict:
        return {
            "prompt": prompt,
            "summary": "TODO: Connect Azure AI Foundry to generate contextual business insights.",
            "suggestions": [
                "Review revenue by region",
                "Investigate top product trends",
                "Prepare a forecast scenario",
            ],
        }
