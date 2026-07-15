# Execute read-only SQL after it has been validated.
# Apply row limits.
# Return rows as dictionaries.
# Log execution time.
import logging
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class QueryRepository:
    """
    Generic read-only SQL executor.

    This repository assumes SQL has already been validated by SQLGuardrailService.
    It does not decide whether SQL is safe.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute_select(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        max_rows: int = 500,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        logger.info("Executing read-only query with max_rows=%s", max_rows)

        result = self.db.execute(text(query), params or {})
        rows = result.fetchmany(max_rows + 1)

        elapsed_ms = (time.perf_counter() - start) * 1000

        truncated = len(rows) > max_rows
        rows = rows[:max_rows]

        output_rows: list[dict[str, Any]] = []
        for row in rows:
            mapping = row._mapping
            output_rows.append({key: _json_safe(value) for key, value in mapping.items()})

        logger.info(
            "Query executed successfully: rows=%s truncated=%s elapsed_ms=%.2f",
            len(output_rows),
            truncated,
            elapsed_ms,
        )

        return {
            "rows": output_rows,
            "row_count": len(output_rows),
            "truncated": truncated,
            "elapsed_ms": elapsed_ms,
        }