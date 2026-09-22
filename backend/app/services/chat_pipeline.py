"""
Everything that happens to a chat request before a provider sees it, plus the
small pieces of the response that do not come from the model.
"""
from app.config import settings
from app.core.sanitize import clean_history, redact_sensitive
from app.models.schemas import ChatRequest, Scheme, SchemeSummary
from app.services import prompts, search
from app.services.providers.base import ChatContext

FOLLOW_UPS = {
    "en": ["Who can apply?", "How do I apply?", "How much will I get?"],
    "pa": ["ਕੌਣ ਅਰਜ਼ੀ ਦੇ ਸਕਦਾ ਹੈ?", "ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਣੀ ਹੈ?", "ਮੈਨੂੰ ਕਿੰਨਾ ਮਿਲੇਗਾ?"],
    "hi": ["कौन आवेदन कर सकता है?", "आवेदन कैसे करें?", "मुझे कितना मिलेगा?"],
}

STARTERS = {
    "en": ["Marriage help for my daughter", "Pension for my parent", "Jobs and skill training"],
    "pa": ["ਧੀ ਦੇ ਵਿਆਹ ਲਈ ਮਦਦ", "ਮਾਪਿਆਂ ਲਈ ਪੈਨਸ਼ਨ", "ਨੌਕਰੀ ਅਤੇ ਹੁਨਰ ਸਿਖਲਾਈ"],
    "hi": ["बेटी की शादी में मदद", "माता-पिता के लिए पेंशन", "नौकरी और कौशल प्रशिक्षण"],
}


def prepare(payload: ChatRequest) -> ChatContext:
    message, redacted = redact_sensitive(payload.message.strip())
    history = clean_history(payload.history, settings.max_history_messages)
    prior_user = [h["content"] for h in history if h["role"] == "user"]

    schemes = search.find_relevant(message, prior_user)
    messages = prompts.build_messages(message, payload.language, history, schemes, redacted)

    return ChatContext(
        message=message,
        language=payload.language,
        history=history,
        schemes=schemes,
        messages=messages,
        redacted=redacted,
    )


def summarize(schemes: list[Scheme], language: str) -> list[SchemeSummary]:
    return [
        SchemeSummary(
            id=s.id,
            name=s.name.get(language, s.name.get("en", "")),
            category=s.category,
            short_description=s.description.get(language, s.description.get("en", "")),
        )
        for s in schemes
    ]


def suggestions_for(schemes: list[Scheme], language: str) -> list[str]:
    table = FOLLOW_UPS if schemes else STARTERS
    return list(table.get(language, table["en"]))
