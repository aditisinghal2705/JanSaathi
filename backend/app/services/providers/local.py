"""
Local provider: answers straight from the scheme records. No keys, no network.

This is NOT an AI model. It is a careful, extractive responder so that:
  * the whole site works today, before Azure is connected,
  * the app still gives a sensible answer if Azure is down (automatic fallback).
It never adds facts: everything it says is copied from schemes.json.
"""
import re
import time
from typing import Iterator

from app.models.schemas import Scheme
from app.services import search
from app.services.providers.base import ChatContext

LABELS = {
    "en": {
        "who": "Who can apply", "get": "What you get", "apply": "How to apply",
        "website": "Official website", "also": "Other schemes that may help",
        "confirm": "Please confirm the details at your nearest Sewa Kendra or with the department before you apply.",
        "privacy": "Please don't share Aadhaar, phone, bank or OTP details in this chat. I removed that number from your message.",
    },
    "pa": {
        "who": "ਕੌਣ ਅਰਜ਼ੀ ਦੇ ਸਕਦਾ ਹੈ", "get": "ਤੁਹਾਨੂੰ ਕੀ ਮਿਲੇਗਾ", "apply": "ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਣੀ ਹੈ",
        "website": "ਸਰਕਾਰੀ ਵੈੱਬਸਾਈਟ", "also": "ਹੋਰ ਸਕੀਮਾਂ ਜੋ ਮਦਦ ਕਰ ਸਕਦੀਆਂ ਹਨ",
        "confirm": "ਅਰਜ਼ੀ ਦੇਣ ਤੋਂ ਪਹਿਲਾਂ ਆਪਣੇ ਨੇੜਲੇ ਸੇਵਾ ਕੇਂਦਰ ਜਾਂ ਵਿਭਾਗ ਤੋਂ ਵੇਰਵਿਆਂ ਦੀ ਪੁਸ਼ਟੀ ਕਰ ਲਓ।",
        "privacy": "ਕਿਰਪਾ ਕਰਕੇ ਇਸ ਚੈਟ ਵਿੱਚ ਆਧਾਰ, ਫ਼ੋਨ, ਬੈਂਕ ਜਾਂ OTP ਦੀ ਜਾਣਕਾਰੀ ਸਾਂਝੀ ਨਾ ਕਰੋ। ਤੁਹਾਡੇ ਸੁਨੇਹੇ ਵਿੱਚੋਂ ਉਹ ਨੰਬਰ ਹਟਾ ਦਿੱਤਾ ਗਿਆ ਹੈ।",
    },
    "hi": {
        "who": "कौन आवेदन कर सकता है", "get": "आपको क्या मिलेगा", "apply": "आवेदन कैसे करें",
        "website": "आधिकारिक वेबसाइट", "also": "अन्य योजनाएँ जो मदद कर सकती हैं",
        "confirm": "आवेदन से पहले अपने नज़दीकी सेवा केंद्र या विभाग से जानकारी की पुष्टि कर लें।",
        "privacy": "कृपया इस चैट में आधार, फ़ोन, बैंक या OTP की जानकारी साझा न करें। आपके संदेश से वह नंबर हटा दिया गया है।",
    },
}

INTRO = {
    "en": "Based on what you told me, **{name}** may help.",
    "pa": "ਤੁਹਾਡੀ ਗੱਲ ਦੇ ਆਧਾਰ 'ਤੇ **{name}** ਤੁਹਾਡੀ ਮਦਦ ਕਰ ਸਕਦੀ ਹੈ।",
    "hi": "आपकी बात के आधार पर **{name}** आपकी मदद कर सकती है।",
}

NO_MATCH = {
    "en": "I couldn't find a matching scheme yet. Tell me who the help is for and what they need, for example marriage, pension, a job, a scholarship or a ration card.",
    "pa": "ਮੈਨੂੰ ਹਾਲੇ ਕੋਈ ਮੇਲ ਖਾਂਦੀ ਸਕੀਮ ਨਹੀਂ ਮਿਲੀ। ਦੱਸੋ ਕਿ ਮਦਦ ਕਿਸ ਲਈ ਚਾਹੀਦੀ ਹੈ ਅਤੇ ਕੀ ਲੋੜ ਹੈ, ਜਿਵੇਂ ਵਿਆਹ, ਪੈਨਸ਼ਨ, ਨੌਕਰੀ, ਵਜ਼ੀਫ਼ਾ ਜਾਂ ਰਾਸ਼ਨ ਕਾਰਡ।",
    "hi": "मुझे अभी कोई मेल खाती योजना नहीं मिली। बताइए कि मदद किसके लिए चाहिए और क्या ज़रूरत है, जैसे शादी, पेंशन, नौकरी, छात्रवृत्ति या राशन कार्ड।",
}

GREETING = {
    "en": "Sat Sri Akal! I'm here to help you find Punjab government schemes. Tell me about your situation, for example marriage help for a daughter, a pension for a parent, a job, a scholarship or a ration card.",
    "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਪੰਜਾਬ ਸਰਕਾਰ ਦੀਆਂ ਸਕੀਮਾਂ ਲੱਭਣ ਵਿੱਚ ਤੁਹਾਡੀ ਮਦਦ ਲਈ ਹਾਜ਼ਰ ਹਾਂ। ਆਪਣੀ ਸਥਿਤੀ ਦੱਸੋ, ਜਿਵੇਂ ਧੀ ਦੇ ਵਿਆਹ ਲਈ ਮਦਦ, ਮਾਪਿਆਂ ਲਈ ਪੈਨਸ਼ਨ, ਨੌਕਰੀ, ਵਜ਼ੀਫ਼ਾ ਜਾਂ ਰਾਸ਼ਨ ਕਾਰਡ।",
    "hi": "सत श्री अकाल! मैं पंजाब सरकार की योजनाएँ खोजने में आपकी मदद के लिए हाज़िर हूँ। अपनी स्थिति बताइए, जैसे बेटी की शादी में सहायता, माता-पिता की पेंशन, नौकरी, छात्रवृत्ति या राशन कार्ड।",
}

# Order matters: "who can apply" contains "apply" but is an eligibility question.
_INTENT_WORDS = {
    "eligibility": [
        "eligible", "eligibility", "qualify", "who can", "criteria", "am i entitled",
        "पात्र", "योग्य", "कौन", "ਯੋਗ", "ਪਾਤਰ", "ਕੌਣ",
    ],
    "benefit": [
        "how much", "amount", "benefit", "money", "get paid", "receive",
        "कितना", "कितनी", "राशि", "मिलेगा", "लाभ", "ਕਿੰਨਾ", "ਕਿੰਨੀ", "ਰਕਮ", "ਮਿਲੇਗਾ", "ਲਾਭ",
    ],
    "apply": [
        "apply", "application", "how do i", "how to", "documents", "form", "register",
        "आवेदन", "अप्लाई", "फॉर्म", "फार्म", "दस्तावेज", "कैसे", "ਅਰਜ਼ੀ", "ਅਪਲਾਈ", "ਫਾਰਮ", "ਦਸਤਾਵੇਜ਼", "ਕਿਵੇਂ",
    ],
}


_INTENT_WORDS = {
    intent: [search.normalize(w) for w in words] for intent, words in _INTENT_WORDS.items()
}


def detect_intent(message: str) -> str | None:
    text = search.normalize(message)
    for intent, words in _INTENT_WORDS.items():
        if any(w in text for w in words):
            return intent
    return None


def _pick(field: dict, language: str) -> str:
    return field.get(language) or field.get("en", "")


def compose_answer(ctx: ChatContext) -> str:
    lang = ctx.language if ctx.language in LABELS else "en"
    labels = LABELS[lang]
    parts: list[str] = []

    if ctx.redacted:
        parts.append(labels["privacy"])

    if not ctx.schemes:
        parts.append(GREETING[lang] if search.is_smalltalk(ctx.message) else NO_MATCH[lang])
        return "\n\n".join(parts)

    primary: Scheme = ctx.schemes[0]
    name = _pick(primary.name, lang)
    intent = detect_intent(ctx.message)

    parts.append(INTRO[lang].format(name=name))

    def line(key: str, field: dict) -> str:
        return f"**{labels[key]}:** {_pick(field, lang)}"

    if intent == "eligibility":
        parts.append(line("who", primary.eligibility))
    elif intent == "benefit":
        parts.append(line("get", primary.benefits))
    elif intent == "apply":
        parts.append(line("apply", primary.how_to_apply))
        if primary.official_link:
            parts.append(f"{labels['website']}: {primary.official_link}")
    else:
        parts.append(_pick(primary.description, lang))
        parts.append(line("who", primary.eligibility))
        parts.append(line("get", primary.benefits))
        parts.append(line("apply", primary.how_to_apply))

    others = ctx.schemes[1:]
    if others:
        bullets = "\n".join(f"- **{_pick(s.name, lang)}**" for s in others)
        parts.append(f"{labels['also']}:\n{bullets}")

    parts.append(labels["confirm"])
    return "\n\n".join(parts)


class LocalProvider:
    name = "local"

    def generate(self, ctx: ChatContext) -> str:
        return compose_answer(ctx)

    def stream(self, ctx: ChatContext) -> Iterator[str]:
        """Yield the answer word by word so the UI behaves the same as with a real model."""
        for piece in re.findall(r"\S+\s*", compose_answer(ctx)):
            yield piece
            time.sleep(0.012)
