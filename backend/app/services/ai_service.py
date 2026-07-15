import logging
from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MAX_SQL_ROWS = 500


@lru_cache
def _get_credential():
    """
    Return a cached azure-identity credential based on AZURE_OPENAI_AUTH_MODE.

    Supported local browser-auth values:
    - interactive
    - azure_ad_interactive

    Default mode uses DefaultAzureCredential.
    """

    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

    settings = get_settings()

    auth_mode = (settings.azure_openai_auth_mode or "").lower()

    logger.info(
        "Creating Azure credential for Azure OpenAI (auth_mode=%s)",
        auth_mode,
    )

    if auth_mode in {"interactive", "azure_ad_interactive"}:
        kwargs: dict[str, str] = {}

        if settings.azure_tenant_id:
            kwargs["tenant_id"] = settings.azure_tenant_id

        if settings.sql_user:
            kwargs["login_hint"] = settings.sql_user

        logger.warning(
            "Using InteractiveBrowserCredential for Azure OpenAI. "
            "This may trigger browser login prompts when a token is required."
        )

        return InteractiveBrowserCredential(**kwargs)

    logger.info("Using DefaultAzureCredential for Azure OpenAI")

    return DefaultAzureCredential(
        managed_identity_client_id=settings.azure_openai_managed_identity_client_id or None
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
    """
    Department-agnostic AI service backed by Azure OpenAI.

    This version no longer relies on hardcoded department repositories as the main AI path.

    Flow:
    1. Get semantic context from metadata catalog.
    2. Build query plan.
    3. Generate SQL.
    4. Validate SQL.
    5. Execute safe read-only query.
    6. Synthesize final business answer.
    """

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    async def analyze(self, prompt: str) -> dict:
        """
        Return an AI-generated analysis grounded in AdventureWorks data.

        This is the new department-agnostic implementation.
        """
        from app.repositories.audit_repository import AuditRepository
        from app.repositories.query_repository import QueryRepository
        from app.services.answer_synthesis_service import AnswerSynthesisService
        from app.services.query_planning_service import QueryPlanningService
        from app.services.semantic_service import SemanticService
        from app.services.sql_generation_service import SQLGenerationService
        from app.services.sql_guardrail_service import SQLGuardrailService

        settings = get_settings()

        if not settings.azure_openai_endpoint or not settings.azure_openai_deployment:
            logger.warning(
                "Azure OpenAI endpoint/deployment not configured; returning mock AI response"
            )
            return self._mock_response(prompt)

        if self.db is None:
            logger.warning("AIService called without database session")
            return {
                "prompt": prompt,
                "summary": "No database session is available, so I cannot query business data right now.",
                "suggestions": [],
            }

        try:
            semantic_service = SemanticService()
            query_planning_service = QueryPlanningService()
            sql_generation_service = SQLGenerationService()
            sql_guardrail_service = SQLGuardrailService()
            query_repository = QueryRepository(self.db)
            answer_synthesis_service = AnswerSynthesisService()
            audit_repository = AuditRepository()

            semantic_context = semantic_service.get_relevant_context(prompt)

            query_plan = query_planning_service.create_plan(
                prompt=prompt,
                semantic_context=semantic_context,
            )

            max_rows = (
                semantic_context
                .get("policies", {})
                .get("policies", {})
                .get("max_rows", MAX_SQL_ROWS)
            )

            generated_sql = sql_generation_service.generate_sql(
                prompt=prompt,
                semantic_context=semantic_context,
                query_plan=query_plan.model_dump(),
                max_rows=max_rows,
            )

            validation = sql_guardrail_service.validate(
                generated_sql,
                max_rows=max_rows,
            )

            if not validation.is_valid or not validation.sanitized_query:
                audit_repository.log_query_event(
                    prompt=prompt,
                    generated_sql=generated_sql,
                    is_valid=False,
                    rejection_reason=validation.rejection_reason,
                    metadata={
                        "query_plan": query_plan.model_dump(),
                    },
                )

                return {
                    "prompt": prompt,
                    "summary": (
                        "I could not safely answer that question using the current data access policy. "
                        f"Reason: {validation.rejection_reason}"
                    ),
                    "suggestions": [
                        "Try asking for aggregated results.",
                        "Avoid requesting individual-level sensitive data.",
                        "Ask for trends, totals, rankings, or grouped summaries.",
                    ],
                }

            execution_result = query_repository.execute_select(
                validation.sanitized_query,
                max_rows=max_rows,
            )

            audit_repository.log_query_event(
                prompt=prompt,
                generated_sql=validation.sanitized_query,
                is_valid=True,
                row_count=execution_result["row_count"],
                elapsed_ms=execution_result["elapsed_ms"],
                metadata={
                    "query_plan": query_plan.model_dump(),
                    "truncated": execution_result.get("truncated", False),
                },
            )

            synthesis_payload = {
                "sql": validation.sanitized_query,
                "row_count": execution_result["row_count"],
                "rows": execution_result["rows"],
                "truncated": execution_result.get("truncated", False),
            }

            summary = answer_synthesis_service.synthesize(
                prompt=prompt,
                result=synthesis_payload,
            )

            return {
                "prompt": prompt,
                "summary": summary,
                "suggestions": [],
            }

        except Exception:
            logger.exception("Azure OpenAI semantic analysis failed")
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