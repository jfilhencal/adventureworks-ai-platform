import logging
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SQLGenerationService:
    """
    Uses Azure OpenAI to generate SQL Server T-SQL from a prompt and semantic context.

    The generated SQL must still be validated by SQLGuardrailService before execution.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_sql(
        self,
        *,
        prompt: str,
        semantic_context: dict[str, Any],
        query_plan: dict[str, Any],
        max_rows: int = 500,
    ) -> str:
        from app.services.ai_service import _get_openai_client

        client = _get_openai_client()

        system_prompt = self._load_prompt_template()

        user_content = {
            "user_question": prompt,
            "semantic_context": semantic_context,
            "query_plan": query_plan,
            "max_rows": max_rows,
        }

        response = client.chat.completions.create(
            model=self.settings.azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": str(user_content),
                },
            ],
            max_completion_tokens=800,
        )

        sql = response.choices[0].message.content or ""
        sql = self._strip_markdown(sql)

        logger.info("Generated SQL: %s", sql)

        return sql

    def _load_prompt_template(self) -> str:
        app_dir = Path(__file__).resolve().parents[1]
        path = app_dir / "prompts" / "sql_generation_prompt.md"

        if path.exists():
            return path.read_text(encoding="utf-8")

        return (
            "You are a SQL Server T-SQL generation assistant. "
            "Generate one safe read-only SELECT query only. "
            "Use only the provided semantic context. "
            "Do not use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, EXEC, stored procedures, comments, or semicolons. "
            "Do not access restricted PII columns. "
            "Use TOP when returning detail rows. "
            "Return only SQL, with no explanation."
        )

    def _strip_markdown(self, text: str) -> str:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")

            if cleaned.lower().startswith("sql"):
                cleaned = cleaned[3:]

        return cleaned.strip()