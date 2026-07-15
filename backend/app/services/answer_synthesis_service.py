import logging
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AnswerSynthesisService:
    """
    Uses Azure OpenAI to convert structured query results into a concise business answer.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def synthesize(
        self,
        *,
        prompt: str,
        result: dict[str, Any],
    ) -> str:
        from app.services.ai_service import _get_openai_client

        client = _get_openai_client()

        system_prompt = self._load_prompt_template()

        response = client.chat.completions.create(
            model=self.settings.azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": str(
                        {
                            "user_question": prompt,
                            "query_result": result,
                        }
                    ),
                },
            ],
            max_completion_tokens=600,
        )

        return response.choices[0].message.content or ""

    def _load_prompt_template(self) -> str:
        app_dir = Path(__file__).resolve().parents[1]
        path = app_dir / "prompts" / "answer_synthesis_prompt.md"

        if path.exists():
            return path.read_text(encoding="utf-8")

        return (
            "You are a business analyst assistant. "
            "Use the provided query results to answer the user's question. "
            "Be concise, factual, and actionable. "
            "Do not invent numbers. "
            "If results are empty, say so clearly."
        )