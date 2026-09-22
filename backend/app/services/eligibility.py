"""
Quick eligibility screening.

Each scheme in schemes.json carries a small `criteria` list derived from its
published eligibility text. A rule is one of:

  {"type": "min_age", "value": 60}
  {"type": "max_age", "value": 35}
  {"type": "gender", "value": ["female"]}
  {"type": "category", "value": ["sc"]}                 social category (any of)
  {"type": "situation", "value": "job_seeker"}          must be ticked
  {"type": "any", "soft": false, "of": [ ...rules ]}    at least one must hold

`soft: true` on an `any` group means "and other notified categories", so a
non-match is reported as "worth checking" rather than a hard no.

Outcomes per rule: met / unmet / unknown (answer not given).
Scheme status:
    unlikely  - at least one rule clearly not met
    maybe     - nothing failed, but some answers were missing or soft
    likely    - every rule met
Income limits are never decided here (the dataset states no numbers); they are
reported in `verify` so the citizen confirms them with the department.

This is a screening aid, not a decision. It never replaces the department's
own verification.
"""
from app.models.schemas import (
    EligibilityMatch,
    EligibilityRequest,
    Reason,
    Scheme,
    SchemeSummary,
)
from app.services import scheme_store

MET, UNMET, UNKNOWN = "met", "unmet", "unknown"


def _eval_rule(rule: dict, profile: EligibilityRequest) -> tuple[str, Reason]:
    rtype = rule["type"]
    value = rule.get("value")

    if rtype in ("min_age", "max_age"):
        reason = Reason(code=rtype, values=[str(value)])
        if profile.age is None:
            return UNKNOWN, reason
        ok = profile.age >= value if rtype == "min_age" else profile.age <= value
        return (MET if ok else UNMET), reason

    if rtype == "gender":
        allowed = value if isinstance(value, list) else [value]
        reason = Reason(code="gender", values=[str(v) for v in allowed])
        if profile.gender is None:
            return UNKNOWN, reason
        return (MET if profile.gender in allowed else UNMET), reason

    if rtype == "category":
        allowed = value if isinstance(value, list) else [value]
        reason = Reason(code="category", values=[str(v) for v in allowed])
        if profile.category is None:
            return UNKNOWN, reason
        return (MET if profile.category in allowed else UNMET), reason

    if rtype == "situation":
        reason = Reason(code="situation", values=[str(value)])
        return (MET if value in profile.situations else UNMET), reason

    if rtype == "any":
        return _eval_any(rule, profile)

    # Unknown rule types must not silently pass.
    return UNKNOWN, Reason(code=rtype, values=[])


def _descriptor(sub_rule: dict) -> str:
    value = sub_rule.get("value")
    if isinstance(value, list):
        value = "|".join(str(v) for v in value)
    return f"{sub_rule['type']}:{value}"


def _eval_any(rule: dict, profile: EligibilityRequest) -> tuple[str, Reason]:
    outcomes = [(_eval_rule(sub, profile), sub) for sub in rule.get("of", [])]
    descriptors = [_descriptor(sub) for _, sub in outcomes]
    reason = Reason(code="any_of", values=descriptors)

    for (state, sub_reason), _sub in outcomes:
        if state == MET:
            return MET, sub_reason
    if any(state == UNKNOWN for (state, _), _ in outcomes):
        return UNKNOWN, reason
    if rule.get("soft"):
        return UNKNOWN, reason
    return UNMET, reason


def evaluate(scheme: Scheme, profile: EligibilityRequest) -> EligibilityMatch:
    lang = profile.language
    met, unmet, verify = [], [], []

    for rule in scheme.criteria:
        state, reason = _eval_rule(rule, profile)
        if state == MET:
            met.append(reason)
        elif state == UNMET:
            unmet.append(reason)
        else:
            verify.append(reason)

    if scheme.income_check:
        verify.append(Reason(code="income_limit", values=[]))

    if unmet:
        status = "unlikely"
    elif any(r.code != "income_limit" for r in verify):
        status = "maybe"
    else:
        status = "likely"

    return EligibilityMatch(
        scheme=SchemeSummary(
            id=scheme.id,
            name=scheme.name.get(lang, scheme.name.get("en", "")),
            category=scheme.category,
            short_description=scheme.description.get(lang, scheme.description.get("en", "")),
        ),
        status=status,
        met=met,
        unmet=unmet,
        verify=verify,
    )


_STATUS_ORDER = {"likely": 0, "maybe": 1, "unlikely": 2}


def screen(profile: EligibilityRequest) -> list[EligibilityMatch]:
    matches = [evaluate(s, profile) for s in scheme_store.load_schemes()]
    matches.sort(key=lambda m: (_STATUS_ORDER[m.status], -len(m.met), m.scheme.name))
    return matches
