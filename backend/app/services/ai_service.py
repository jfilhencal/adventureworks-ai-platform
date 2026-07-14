import logging
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _get_openai_client():
    """Build an AzureOpenAI client authenticated via Microsoft Entra ID (no API keys).

    Uses DefaultAzureCredential so the same code works with `az login` locally and
    with a Container Apps/App Service managed identity in Azure.
    """
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI

    settings = get_settings()
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_openai_managed_identity_client_id or None
    )
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.azure_openai_api_version,
    )


class AIService:
    """Generative AI service backed by Azure AI Foundry / Azure OpenAI."""

    async def analyze(self, prompt: str) -> dict:
        """Return an AI-generated analysis, falling back to a mock payload when Foundry isn't configured."""
        settings = get_settings()
        if not settings.azure_openai_endpoint or not settings.azure_openai_deployment:
            logger.warning("Azure OpenAI endpoint/deployment not configured; returning mock AI response")
            return self._mock_response(prompt)

        try:
            client = _get_openai_client()
            response = client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a business analyst assistant for the AdventureWorks AI Platform. "
                            "Provide concise, actionable insights based on the user's request."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
            )
            summary = response.choices[0].message.content or ""
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
