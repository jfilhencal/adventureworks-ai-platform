from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.audit_repository import AuditRepository
from app.repositories.query_repository import QueryRepository
from app.schemas.query import (
    QueryExecutionRequest,
    QueryExecutionResponse,
    QueryPreviewRequest,
    QueryPreviewResponse,
)
from app.services.query_planning_service import QueryPlanningService
from app.services.semantic_service import SemanticService
from app.services.sql_generation_service import SQLGenerationService
from app.services.sql_guardrail_service import SQLGuardrailService

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/execute", response_model=QueryExecutionResponse)
def execute_query(
    request: QueryExecutionRequest,
    db: Session = Depends(get_db),
) -> QueryExecutionResponse:
    guardrails = SQLGuardrailService()
    validation = guardrails.validate(
        request.query,
        max_rows=request.max_rows,
    )

    if not validation.is_valid or not validation.sanitized_query:
        raise HTTPException(
            status_code=400,
            detail=validation.rejection_reason,
        )

    repository = QueryRepository(db)

    result = repository.execute_select(
        validation.sanitized_query,
        params=request.params,
        max_rows=request.max_rows,
    )

    AuditRepository().log_query_event(
        prompt="manual_query_execution",
        generated_sql=validation.sanitized_query,
        is_valid=True,
        row_count=result["row_count"],
        elapsed_ms=result["elapsed_ms"],
    )

    return QueryExecutionResponse(
        query=validation.sanitized_query,
        row_count=result["row_count"],
        rows=result["rows"],
        elapsed_ms=result["elapsed_ms"],
    )


@router.post("/preview", response_model=QueryPreviewResponse)
def preview_ai_query(
    request: QueryPreviewRequest,
    db: Session = Depends(get_db),
) -> QueryPreviewResponse:
    semantic_service = SemanticService()
    query_planning_service = QueryPlanningService()
    sql_generation_service = SQLGenerationService()
    sql_guardrail_service = SQLGuardrailService()
    audit_repository = AuditRepository()

    semantic_context = semantic_service.get_relevant_context(request.prompt)

    query_plan = query_planning_service.create_plan(
        prompt=request.prompt,
        semantic_context=semantic_context,
    )

    generated_sql = sql_generation_service.generate_sql(
        prompt=request.prompt,
        semantic_context=semantic_context,
        query_plan=query_plan.model_dump(),
        max_rows=request.max_rows,
    )

    validation = sql_guardrail_service.validate(
        generated_sql,
        max_rows=request.max_rows,
    )

    rows: list[dict] = []

    if request.execute:
        if not validation.is_valid or not validation.sanitized_query:
            audit_repository.log_query_event(
                prompt=request.prompt,
                generated_sql=generated_sql,
                is_valid=False,
                rejection_reason=validation.rejection_reason,
                metadata={
                    "query_plan": query_plan.model_dump(),
                },
            )

            return QueryPreviewResponse(
                prompt=request.prompt,
                semantic_context=semantic_context,
                query_plan=query_plan.model_dump(),
                generated_sql=generated_sql,
                validation=validation,
                rows=[],
            )

        result = QueryRepository(db).execute_select(
            validation.sanitized_query,
            max_rows=request.max_rows,
        )

        rows = result["rows"]

        audit_repository.log_query_event(
            prompt=request.prompt,
            generated_sql=validation.sanitized_query,
            is_valid=True,
            row_count=result["row_count"],
            elapsed_ms=result["elapsed_ms"],
            metadata={
                "query_plan": query_plan.model_dump(),
                "truncated": result.get("truncated", False),
            },
        )

    return QueryPreviewResponse(
        prompt=request.prompt,
        semantic_context=semantic_context,
        query_plan=query_plan.model_dump(),
        generated_sql=generated_sql,
        validation=validation,
        rows=rows,
    )