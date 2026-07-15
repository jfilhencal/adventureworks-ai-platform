from pydantic import BaseModel, Field


class MetricDefinition(BaseModel):
    name: str
    business_name: str | None = None
    description: str | None = None
    domain: str | None = None
    base_table: str
    expression: str
    default_alias: str | None = None
    semantic_type: str | None = None
    suggested_filter: str | None = None
    synonyms: list[str] = Field(default_factory=list)