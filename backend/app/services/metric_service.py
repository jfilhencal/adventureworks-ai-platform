from typing import Any

from app.repositories.catalog_repository import CatalogRepository


class MetricService:
    """
    Department-agnostic metric lookup service.

    Metrics are loaded from app/semantic/metrics.yaml through CatalogRepository.
    """

    def __init__(self, catalog_repository: CatalogRepository | None = None) -> None:
        self.catalog_repository = catalog_repository or CatalogRepository()

    def get_metrics(self) -> list[dict[str, Any]]:
        return self.catalog_repository.get_metrics()

    def get_metric(self, name: str) -> dict[str, Any] | None:
        normalized = name.lower()

        for metric in self.get_metrics():
            if metric.get("name", "").lower() == normalized:
                return metric

        return None

    def search_metrics(self, text: str) -> list[dict[str, Any]]:
        normalized = text.lower()
        matches: list[dict[str, Any]] = []

        for metric in self.get_metrics():
            candidates = [
                metric.get("name", ""),
                metric.get("business_name", ""),
                metric.get("description", ""),
                metric.get("domain", ""),
                *metric.get("synonyms", []),
            ]

            if any(
                candidate
                and (
                    candidate.lower() in normalized
                    or normalized in candidate.lower()
                )
                for candidate in candidates
            ):
                matches.append(metric)

        return matches