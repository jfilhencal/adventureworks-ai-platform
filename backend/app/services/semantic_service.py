import logging
from typing import Any

from app.repositories.catalog_repository import CatalogRepository

logger = logging.getLogger(__name__)


class SemanticService:
    """
    Department-agnostic semantic lookup service.

    Given a user prompt, returns relevant tables, columns, metrics, joins, and policies.
    First version uses keyword matching. Later this can be replaced with embeddings.
    """

    def __init__(self, catalog_repository: CatalogRepository | None = None) -> None:
        self.catalog_repository = catalog_repository or CatalogRepository()

    def get_relevant_context(self, prompt: str) -> dict[str, Any]:
        normalized_prompt = prompt.lower()

        tables = self.catalog_repository.get_tables()
        columns = self.catalog_repository.get_columns()
        metrics = self.catalog_repository.get_metrics()
        joins = self.catalog_repository.get_joins()
        policies = self.catalog_repository.get_policies()
        synonyms = self.catalog_repository.get_synonyms()

        expanded_terms = self._expand_terms(normalized_prompt, synonyms)

        relevant_metrics = [
            metric
            for metric in metrics
            if self._matches_metric(metric, expanded_terms)
        ]

        relevant_tables = [
            table
            for table in tables
            if self._matches_table(table, expanded_terms)
        ]

        relevant_columns = [
            column
            for column in columns
            if self._matches_column(column, expanded_terms)
        ]

        table_names = {
            table["name"]
            for table in relevant_tables
            if table.get("name")
        }

        for metric in relevant_metrics:
            if metric.get("base_table"):
                table_names.add(metric["base_table"])

        for column in relevant_columns:
            if column.get("table"):
                table_names.add(column["table"])

        if not table_names:
            table_names = self._default_table_selection(expanded_terms)

        relevant_tables = [
            table
            for table in tables
            if table.get("name") in table_names
        ]

        relevant_columns = [
            column
            for column in columns
            if column.get("table") in table_names
        ]

        relevant_joins = [
            join
            for join in joins
            if join.get("left_table") in table_names
            or join.get("right_table") in table_names
        ]

        context = {
            "prompt": prompt,
            "expanded_terms": sorted(expanded_terms),
            "tables": relevant_tables,
            "columns": relevant_columns,
            "metrics": relevant_metrics,
            "joins": relevant_joins,
            "policies": policies,
        }

        logger.info(
            "Semantic context selected: tables=%s metrics=%s joins=%s",
            len(relevant_tables),
            len(relevant_metrics),
            len(relevant_joins),
        )

        return context

    def _expand_terms(
        self,
        normalized_prompt: str,
        synonyms: dict[str, list[str]],
    ) -> set[str]:
        terms = set(
            normalized_prompt
            .replace(",", " ")
            .replace("?", " ")
            .replace(".", " ")
            .replace(":", " ")
            .replace(";", " ")
            .split()
        )

        for canonical, values in synonyms.items():
            all_terms = {
                canonical.lower(),
                *[value.lower() for value in values],
            }

            if any(term in normalized_prompt for term in all_terms):
                terms.update(all_terms)

        return terms

    def _matches_metric(self, metric: dict[str, Any], terms: set[str]) -> bool:
        candidates = {
            metric.get("name", ""),
            metric.get("business_name", ""),
            metric.get("description", ""),
            metric.get("domain", ""),
            *metric.get("synonyms", []),
        }

        return self._matches_candidates(candidates, terms)

    def _matches_table(self, table: dict[str, Any], terms: set[str]) -> bool:
        candidates = {
            table.get("name", ""),
            table.get("business_name", ""),
            table.get("domain", ""),
            table.get("subject_area", ""),
            table.get("description", ""),
        }

        return self._matches_candidates(candidates, terms)

    def _matches_column(self, column: dict[str, Any], terms: set[str]) -> bool:
        candidates = {
            column.get("name", ""),
            column.get("business_name", ""),
            column.get("description", ""),
            column.get("semantic_type", ""),
            *column.get("synonyms", []),
        }

        return self._matches_candidates(candidates, terms)

    def _matches_candidates(self, candidates: set[str], terms: set[str]) -> bool:
        text = " ".join(
            candidate.lower()
            for candidate in candidates
            if candidate
        )

        return any(term in text for term in terms)

    def _default_table_selection(self, terms: set[str]) -> set[str]:
        sales_terms = {
            "sales",
            "revenue",
            "orders",
            "customer",
            "client",
            "product",
            "region",
            "market",
            "territory",
        }

        workforce_terms = {
            "employee",
            "employees",
            "headcount",
            "staff",
            "department",
            "tenure",
            "workforce",
            "hiring",
            "hires",
        }

        if terms.intersection(workforce_terms):
            return {"dbo.DimEmployee"}
        if terms.intersection(sales_terms):
            return {
                "dbo.FactInternetSales",
                "dbo.DimProduct",
                "dbo.DimCustomer",
                "dbo.DimSalesTerritory",
                "dbo.DimGeography",
            }

        return {
            "dbo.FactInternetSales",
            "dbo.DimProduct",
            "dbo.DimCustomer",
            "dbo.DimSalesTerritory",
        }
