from fastapi import APIRouter, Depends

from app.core.rate_limit import rate_limited
from app.models.schemas import EligibilityRequest, EligibilityResponse
from app.services import eligibility

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])


@router.post("", response_model=EligibilityResponse)
def check_eligibility(payload: EligibilityRequest, _: None = Depends(rate_limited)):
    """
    Quick screening against every scheme. Returns all schemes grouped by status
    (likely / maybe / unlikely) with machine-readable reasons the UI translates.
    This is a screening aid; the department makes the final decision.
    """
    return EligibilityResponse(results=eligibility.screen(payload))
