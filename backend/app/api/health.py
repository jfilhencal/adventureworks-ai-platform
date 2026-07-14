import logging

from fastapi import APIRouter

from app.core.database import verify_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """Health endpoint used by deployment and monitoring.
    
    Returns:
        Dictionary with service and database status
    """
    db_healthy = verify_connection()
    status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": status,
        "service": "backend",
        "database": "ok" if db_healthy else "error",
    }
