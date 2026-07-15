from typing import Any

from pydantic import BaseModel, Field


class SQLValidationResult(BaseModel):
    is_valid: bool
    sanitized_query: str | None = None
    rejection_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)


class QueryExecutionRequest(BaseModel):
    query: str
    params: dict[str, Any] | None = None
    max_rows: int = 500


class QueryExecutionResponse(BaseModel):
    query: str
    row_count: int
    rows: list[dict[str, Any]]
    elapsed_ms: float


class QueryPreviewRequest(BaseModel):
    prompt: str
    execute: bool = False
    max_rows: int = 100


class QueryPreviewResponse(BaseModel):
    prompt: str
    semantic_context: dict[str, Any]
    query_plan: dict[str, Any]
    generated_sql: str | None
    validation: SQLValidationResult
    rows: list[dict[str, Any]] = Field(default_factory=list)