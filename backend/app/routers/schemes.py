from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import Scheme, SchemeListResponse, SchemePublic
from app.services import scheme_store

router = APIRouter(prefix="/api/schemes", tags=["schemes"])

_INTERNAL_FIELDS = {"keywords", "criteria", "income_check"}


def to_public(scheme: Scheme) -> SchemePublic:
    return SchemePublic(**scheme.model_dump(exclude=_INTERNAL_FIELDS))


@router.get("", response_model=SchemeListResponse)
def list_schemes(
    category: str | None = Query(default=None, description="Category id (e.g. 'pension') or English name"),
    search: str | None = Query(default=None, description="Matches any language, plus keywords"),
):
    results = [to_public(s) for s in scheme_store.get_all(category=category, search=search)]
    return SchemeListResponse(total=len(results), results=results)


@router.get("/{scheme_id}", response_model=SchemePublic)
def get_scheme(scheme_id: str):
    scheme = scheme_store.get_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return to_public(scheme)
