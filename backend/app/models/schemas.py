from typing import Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["en", "pa", "hi"]
Localized = dict[str, str]  # {"en": ..., "pa": ..., "hi": ...}


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    language: Language = "en"
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)


class SchemeSummary(BaseModel):
    id: str
    name: str
    category: str
    short_description: str


class ChatResponse(BaseModel):
    reply: str
    matched_schemes: list[SchemeSummary] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    provider: str = "local"
    degraded: bool = False  # True when Azure failed and the local answer was used


# --------------------------------------------------------------------------
# Schemes
# --------------------------------------------------------------------------
class SchemePublic(BaseModel):
    id: str
    category: str
    department: str
    name: Localized
    description: Localized
    eligibility: Localized
    benefits: Localized
    how_to_apply: Localized
    official_link: Optional[str] = None


class Scheme(SchemePublic):
    """Full record as stored on disk, including search + screening metadata."""
    keywords: list[str] = Field(default_factory=list)
    income_check: bool = False
    criteria: list[dict] = Field(default_factory=list)


class SchemeListResponse(BaseModel):
    total: int
    results: list[SchemePublic]


class Category(BaseModel):
    id: str
    name: Localized
    blurb: Localized
    icon: str
    scheme_count: int = 0


class CategoryListResponse(BaseModel):
    results: list[Category]


# --------------------------------------------------------------------------
# Eligibility screening
# --------------------------------------------------------------------------
Gender = Literal["female", "male", "other"]
SocialCategory = Literal["sc", "bc", "general", "other"]
Situation = Literal[
    "punjab_resident_3y",
    "student_post_matric",
    "job_seeker",
    "widow_or_destitute_woman",
    "construction_worker_family",
    "daughter_marriage_planned",
    "bpl_or_nfsa_household",
]


class EligibilityRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=120)
    gender: Optional[Gender] = None
    category: Optional[SocialCategory] = None
    situations: list[Situation] = Field(default_factory=list)
    language: Language = "en"


class Reason(BaseModel):
    """
    Machine-readable explanation; the frontend turns it into a sentence in the
    user's language.  code is one of: min_age, max_age, gender, category,
    situation, any_of, income_limit.  values are raw strings (e.g. "60", "sc",
    or "situation:widow_or_destitute_woman" inside any_of).
    """
    code: str
    values: list[str] = Field(default_factory=list)


class EligibilityMatch(BaseModel):
    scheme: SchemeSummary
    status: Literal["likely", "maybe", "unlikely"]
    met: list[Reason] = Field(default_factory=list)
    unmet: list[Reason] = Field(default_factory=list)
    verify: list[Reason] = Field(default_factory=list)


class EligibilityResponse(BaseModel):
    results: list[EligibilityMatch]


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    provider: str          # provider that answers chat requests right now
    ai_ready: bool         # True only when a real AI model is connected
    schemes: int
