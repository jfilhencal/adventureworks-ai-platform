from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    """Request payload for department-agnostic AI analysis."""

    prompt: str = Field(
        ...,
        min_length=3,
        description="User prompt for AI analysis",
    )


class AIAnalysisResponse(BaseModel):
    """Response payload for department-agnostic AI analysis."""

    prompt: str = Field(..., description="Original user prompt")
    summary: str = Field(..., description="AI-generated business summary")
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions or actions",
    )
    sql: str | None = Field(
        default=None,
        description="Generated SQL used to answer the prompt, if available",
    )
    row_count: int | None = Field(
        default=None,
        description="Number of rows used for the analysis",
    )
    debug: dict | None = Field(
        default=None,
        description="Debug metadata such as query plan and semantic context",
    )