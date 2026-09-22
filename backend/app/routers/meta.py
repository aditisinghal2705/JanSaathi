from fastapi import APIRouter, Depends

from app import __version__
from app.core.rate_limit import rate_limited
from app.models.schemas import CategoryListResponse, HealthResponse
from app.services import ai_service, scheme_store

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        service="jansaathi-api",
        version=__version__,
        provider=ai_service.active_provider_name(),
        ai_ready=ai_service.is_ai_ready(),
        schemes=len(scheme_store.load_schemes()),
    )


@router.get("/categories", response_model=CategoryListResponse)
def categories():
    return CategoryListResponse(results=scheme_store.get_categories())


@router.get("/ai/status")
def ai_status(_: None = Depends(rate_limited)):
    """
    Makes one tiny live call to your Azure deployment and reports the result.
    Use it right after setting the AZURE_OPENAI_* variables:
        curl http://localhost:8000/api/ai/status
    """
    return ai_service.ping()
