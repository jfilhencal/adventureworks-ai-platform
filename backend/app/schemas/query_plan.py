from typing import Any

from pydantic import BaseModel, Field


class QueryPlan(BaseModel):
    prompt: str
    intent: str = "ad_hoc_analysis"
    selected_domains: list[str] = Field(default_factory=list)
    selected_tables: list[str] = Field(default_factory=list)
    selected_metrics: list[str] = Field(default_factory=list)
    selected_dimensions: list[str] = Field(default_factory=list)
    selected_joins: list[dict[str, Any]] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    policies: dict[str, Any] = Field(default_factory=dict)