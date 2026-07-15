import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CatalogRepository:
    """
    Loads semantic metadata from YAML files under app/semantic.

    This is intentionally file-based for version control and easy review.
    Later, this can be replaced by database-backed metadata tables.
    """

    def __init__(self, semantic_dir: Path | None = None) -> None:
        app_dir = Path(__file__).resolve().parents[1]
        self.semantic_dir = semantic_dir or app_dir / "semantic"

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = self.semantic_dir / filename

        if not path.exists():
            logger.warning("Semantic file not found: %s", path)
            return {}

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        return data

    @lru_cache(maxsize=1)
    def get_catalog(self) -> dict[str, Any]:
        return self._load_yaml("catalog.yaml")

    @lru_cache(maxsize=1)
    def get_metrics_file(self) -> dict[str, Any]:
        return self._load_yaml("metrics.yaml")

    @lru_cache(maxsize=1)
    def get_joins_file(self) -> dict[str, Any]:
        return self._load_yaml("joins.yaml")

    @lru_cache(maxsize=1)
    def get_policies_file(self) -> dict[str, Any]:
        return self._load_yaml("policies.yaml")

    @lru_cache(maxsize=1)
    def get_synonyms_file(self) -> dict[str, Any]:
        return self._load_yaml("synonyms.yaml")

    def get_tables(self) -> list[dict[str, Any]]:
        return self.get_catalog().get("tables", [])

    def get_columns(self) -> list[dict[str, Any]]:
        return self.get_catalog().get("columns", [])

    def get_metrics(self) -> list[dict[str, Any]]:
        return self.get_metrics_file().get("metrics", [])

    def get_joins(self) -> list[dict[str, Any]]:
        return self.get_joins_file().get("joins", [])

    def get_policies(self) -> dict[str, Any]:
        return self.get_policies_file()

    def get_synonyms(self) -> dict[str, Any]:
        return self.get_synonyms_file().get("synonyms", {})

    def get_all(self) -> dict[str, Any]:
        return {
            "tables": self.get_tables(),
            "columns": self.get_columns(),
            "metrics": self.get_metrics(),
            "joins": self.get_joins(),
            "policies": self.get_policies(),
            "synonyms": self.get_synonyms(),
        }