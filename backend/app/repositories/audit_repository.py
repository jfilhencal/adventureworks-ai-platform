import logging
from typing import Any

logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Audit logger.

    This currently logs to application logs. 
    """

    def log_query_event(
        self,
        *,
        prompt: str,
        generated_sql: str | None,
        is_valid: bool,
        rejection_reason: str | None = None,
        row_count: int | None = None,
        elapsed_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "AI_QUERY_AUDIT prompt=%r is_valid=%s row_count=%s elapsed_ms=%s rejection=%r metadata=%s sql=%r",
            prompt,
            is_valid,
            row_count,
            elapsed_ms,
            rejection_reason,
            metadata or {},
            generated_sql,
        )