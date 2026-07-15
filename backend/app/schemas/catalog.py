from typing import Any

from pydantic import BaseModel, Field


class CatalogTable(BaseModel):
    name: str
    business_name: str | None = None
    domain: str | None = None
    subject_area: str | None = None
    description: str | None = None
    grain: str | None = None
    allowed_for_ai: bool = True
    default_date_column: str | None = None
    pii_level: str | None = None


class CatalogColumn(BaseModel):
    table: str
    name: str
    business_name: str | None = None
    description: str | None = None
    semantic_type: str | None = None
    allowed_for_ai: bool = True
    is_pii: bool = False
    synonyms: list[str] = Field(default_factory=list)


class SemanticContextResponse(BaseModel):
    prompt: str
    tables: list[dict[str, Any]]
    columns: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    joins: list[dict[str, Any]]
    policies: dict[str, Any]