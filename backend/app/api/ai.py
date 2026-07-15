from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai import AIAnalysisRequest
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze")
async def analyze_prompt(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Department-agnostic AI analysis endpoint.

    This endpoint uses:
    - semantic catalog
    - query planning
    - SQL generation
    - SQL guardrails
    - read-only query execution
    - answer synthesis
    """
    service = AIService(db)
    return await service.analyze(request.prompt)