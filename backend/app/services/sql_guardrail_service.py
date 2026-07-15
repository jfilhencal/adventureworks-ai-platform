# Validate generated SQL before execution.
# SQL must start with SELECT or WITH.
# No semicolons.
# No comments.
# No DDL/DML keywords.
# No stored procedure calls.
# No INSERT, UPDATE, DELETE, DROP, ALTER, MERGE, TRUNCATE, etc.
# Only one statement.
# Enforce TOP or wrap query with limit behavior.
# Block restricted tables/columns.
# Block direct employee-level PII unless explicitly allowed.
# Log rejected queries.

import logging
import re
from typing import Any

from app.repositories.catalog_repository import CatalogRepository
from app.schemas.query import SQLValidationResult

logger = logging.getLogger(__name__)


_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|EXECUTE|MERGE|TRUNCATE|GRANT|REVOKE|"
    r"BACKUP|RESTORE|SHUTDOWN|WAITFOR|OPENROWSET|OPENQUERY|OPENDATASOURCE|BULK|INTO)\b|"
    r"\bsp_\w+|\bxp_\w+|--|/\*|\*/|;",
    re.IGNORECASE,
)

_SELECT_OR_WITH_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class SQLGuardrailService:
    """
    Validates AI-generated SQL before execution.

    This is intentionally conservative. The model can generate SQL, but this service
    decides whether the SQL is allowed to run.
    """

    def __init__(self, catalog_repository: CatalogRepository | None = None) -> None:
        self.catalog_repository = catalog_repository or CatalogRepository()

    def validate(self, query: str, max_rows: int | None = None) -> SQLValidationResult:
        if not query or not query.strip():
            return SQLValidationResult(
                is_valid=False,
                rejection_reason="Query is empty.",
            )

        sanitized = query.strip()

        if not _SELECT_OR_WITH_PATTERN.search(sanitized):
            return SQLValidationResult(
                is_valid=False,
                rejection_reason="Only SELECT or WITH queries are allowed.",
            )

        if _FORBIDDEN_SQL_PATTERN.search(sanitized):
            return SQLValidationResult(
                is_valid=False,
                rejection_reason="Query contains forbidden SQL syntax or keywords.",
            )

        policies = self.catalog_repository.get_policies()
        restricted_tables = {
            table.lower()
            for table in policies.get("restricted_tables", [])
        }

        restricted_columns = policies.get("restricted_columns", [])
        allow_employee_level_data = policies.get("policies", {}).get(
            "allow_employee_level_data",
            False,
        )

        lower_query = sanitized.lower()

        for table in restricted_tables:
            if table.lower() in lower_query and not allow_employee_level_data:
                if not self._appears_aggregate_query(lower_query):
                    return SQLValidationResult(
                        is_valid=False,
                        rejection_reason=(
                            f"Query references restricted table '{table}' without aggregate analysis."
                        ),
                    )

        for item in restricted_columns:
            table = item.get("table", "")
            columns = item.get("columns", [])

            for column in columns:
                if column.lower() in lower_query:
                    return SQLValidationResult(
                        is_valid=False,
                        rejection_reason=(
                            f"Query references restricted column '{table}.{column}'."
                        ),
                    )

        allowed_tables = {
            table.lower()
            for table in policies.get("allowed_tables", [])
        }

        if allowed_tables:
            unknown_table = self._find_unknown_table_reference(
                lower_query=lower_query,
                allowed_tables=allowed_tables,
            )
            if unknown_table:
                return SQLValidationResult(
                    is_valid=False,
                    rejection_reason=f"Query references a table that is not allowed: {unknown_table}",
                )

        warnings: list[str] = []

        if max_rows:
            warnings.append(f"Execution will be capped at {max_rows} rows.")

        return SQLValidationResult(
            is_valid=True,
            sanitized_query=sanitized,
            warnings=warnings,
        )

    def _appears_aggregate_query(self, lower_query: str) -> bool:
        aggregate_keywords = [
            "count(",
            "count_big(",
            "sum(",
            "avg(",
            "min(",
            "max(",
            "group by",
        ]
        return any(keyword in lower_query for keyword in aggregate_keywords)

    def _find_unknown_table_reference(
        self,
        *,
        lower_query: str,
        allowed_tables: set[str],
    ) -> str | None:
        """
        Best-effort table reference detection.

        This is not a full SQL parser. It checks common FROM/JOIN table references.
        """

        table_refs = re.findall(
            r"\b(?:from|join)\s+([a-zA-Z0-9_\.\[\]]+)",
            lower_query,
            re.IGNORECASE,
        )

        normalized_allowed = {
            table.replace("[", "").replace("]", "").lower()
            for table in allowed_tables
        }

        for table_ref in table_refs:
            normalized_ref = table_ref.replace("[", "").replace("]", "").lower()

            if normalized_ref not in normalized_allowed:
                return table_ref

        return None