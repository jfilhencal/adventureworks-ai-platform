from fastapi import APIRouter

from app.schemas.sales import AIAnalysisRequest
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze")
async def analyze_prompt(request: AIAnalysisRequest) -> dict:
    """Accept an AI analysis request and return a mock response."""
    service = AIService()
    return await service.analyze(request.prompt)
