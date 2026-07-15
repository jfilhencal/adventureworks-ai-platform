from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sales import AIAnalysisRequest
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze")
async def analyze_prompt(request: AIAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """Accept an AI analysis request and return an AI-generated (or mock) response."""
    service = AIService(db)
    return await service.analyze(request.prompt)
