from fastapi import APIRouter, HTTPException

from app.services.metric_service import MetricService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics() -> list:
    service = MetricService()
    return service.get_metrics()


@router.get("/search")
def search_metrics(q: str) -> list:
    service = MetricService()
    return service.search_metrics(q)


@router.get("/{metric_name}")
def get_metric(metric_name: str) -> dict:
    service = MetricService()
    metric = service.get_metric(metric_name)

    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    return metric