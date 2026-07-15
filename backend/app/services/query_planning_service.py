import logging
from typing import Any

from app.schemas.query_plan import QueryPlan

logger = logging.getLogger(__name__)


class QueryPlanningService:
    """
    Creates a department-agnostic query plan from semantic context.

    First version is deterministic and metadata-driven.
    Later, this can become an LLM-assisted planning step.
    """

    def create_plan(
        self,
        *,
        prompt: str,
        semantic_context: dict[str, Any],
    ) -> QueryPlan:
        tables = semantic_context.get("tables", [])
        metrics = semantic_context.get("metrics", [])
        columns = semantic_context.get("columns", [])
        joins = semantic_context.get("joins", [])
        policies = semantic_context.get("policies", {})

        selected_tables = [
            table["name"]
            for table in tables
            if table.get("name")
        ]

        selected_metrics = [
            metric["name"]
            for metric in metrics
            if metric.get("name")
        ]

        selected_dimensions = self._select_dimensions(
            prompt=prompt,
            columns=columns,
        )

        selected_domains = sorted(
            {
                table.get("domain")
                for table in tables
                if table.get("domain")
            }
        )

        plan = QueryPlan(
            prompt=prompt,
            intent="ad_hoc_analysis",
            selected_domains=selected_domains,
            selected_tables=selected_tables,
            selected_metrics=selected_metrics,
            selected_dimensions=selected_dimensions,
            selected_joins=joins,
            filters={},
            policies=policies.get("policies", policies),
        )

        logger.info(
            "Query plan created: tables=%s metrics=%s dimensions=%s",
            len(plan.selected_tables),
            len(plan.selected_metrics),
            len(plan.selected_dimensions),
        )

        return plan

    def _select_dimensions(
        self,
        *,
        prompt: str,
        columns: list[dict[str, Any]],
    ) -> list[str]:
        normalized_prompt = prompt.lower()
        dimensions: list[str] = []

        for column in columns:
            semantic_type = column.get("semantic_type")

            if semantic_type not in {"text", "date"}:
                continue

            candidates = [
                column.get("name", ""),
                column.get("business_name", ""),
                *column.get("synonyms", []),
            ]

            if any(
                candidate
                and candidate.lower() in normalized_prompt
                for candidate in candidates
            ):
                table_name = column.get("table")
                column_name = column.get("name")

                if table_name and column_name:
                    dimensions.append(f"{table_name}.{column_name}")

        return dimensions