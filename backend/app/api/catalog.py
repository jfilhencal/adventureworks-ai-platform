from fastapi import APIRouter

from app.repositories.catalog_repository import CatalogRepository
from app.services.semantic_service import SemanticService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/all")
def get_catalog() -> dict:
    repository = CatalogRepository()
    return repository.get_all()


@router.get("/tables")
def get_tables() -> list:
    repository = CatalogRepository()
    return repository.get_tables()


@router.get("/columns")
def get_columns() -> list:
    repository = CatalogRepository()
    return repository.get_columns()


@router.get("/metrics")
def get_metrics() -> list:
    repository = CatalogRepository()
    return repository.get_metrics()


@router.get("/joins")
def get_joins() -> list:
    repository = CatalogRepository()
    return repository.get_joins()


@router.get("/policies")
def get_policies() -> dict:
    repository = CatalogRepository()
    return repository.get_policies()


@router.get("/context")
def get_context(prompt: str) -> dict:
    service = SemanticService()
    return service.get_relevant_context(prompt)