"""
AI provider layer for JanSaathi.

Uses the JanSaathi Azure AI Foundry Agent when AI_PROVIDER=azure.
Falls back to the local provider if Azure fails.
"""

import logging
from dataclasses import dataclass
from typing import Iterator

from app.config import settings
from app.models.schemas import ChatMessage, Scheme
from app.services import prompts
from app.services.providers.base import ChatContext
from app.services.providers.local import LocalProvider
from app.azure_agent import ask_jansathi

log = logging.getLogger("jansaathi.ai")

_local = LocalProvider()


def active_provider_name() -> str:
    return settings.effective_provider


def is_ai_ready() -> bool:
    return settings.effective_provider == "azure"


def startup_report() -> str:
    if settings.effective_provider == "azure":
        return "AI provider: Azure AI Foundry Agent (JanSathi v6)"

    return "AI provider: local (retrieval-only). Set AI_PROVIDER=azure to use Azure AI Foundry."


# ------------------------------------------------------------------
# Non-streaming
# ------------------------------------------------------------------

@dataclass
class ChatResult:
    text: str
    provider: str
    degraded: bool = False


def generate_chat(ctx: ChatContext) -> ChatResult:

    if active_provider_name() == "azure":
        try:
            answer = ask_jansathi(ctx.message)

            if not answer or not answer.strip():
                raise RuntimeError("JanSaathi Agent returned an empty response.")

            return ChatResult(
                text=answer.strip(),
                provider="azure",
                degraded=False,
            )

        except Exception:
            log.exception(
                "Azure JanSaathi Agent failed; falling back to local provider."
            )

            return ChatResult(
                text=_local.generate(ctx),
                provider="local",
                degraded=True,
            )

    return ChatResult(
        text=_local.generate(ctx),
        provider="local",
        degraded=False,
    )


# ------------------------------------------------------------------
# Streaming
# ------------------------------------------------------------------

class ChatStream:
    """
    Streaming interface.

    The current JanSaathi Foundry Agent helper returns a complete response,
    rather than token-by-token streaming, so Azure is returned as one chunk.
    """

    def __init__(self, ctx: ChatContext):
        self.ctx = ctx
        self.provider = active_provider_name()
        self.degraded = False
        self.interrupted = False

    def __iter__(self) -> Iterator[str]:

        if self.provider == "azure":

            try:
                answer = ask_jansathi(self.ctx.message)

                if not answer or not answer.strip():
                    raise RuntimeError(
                        "JanSaathi Agent returned an empty response."
                    )

                yield answer.strip()
                return

            except Exception:
                log.exception(
                    "Azure JanSaathi Agent failed; falling back to local provider."
                )

                self.provider = "local"
                self.degraded = True

        yield from _local.stream(self.ctx)


def open_stream(ctx: ChatContext) -> ChatStream:
    return ChatStream(ctx)


# ------------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------------

def ping() -> dict:
    """
    Check connectivity with the JanSaathi Azure AI Foundry Agent.
    """

    if settings.ai_provider != "azure":
        return {
            "ok": False,
            "provider": "local",
            "detail": "AI_PROVIDER is not 'azure'.",
        }

    try:
        answer = ask_jansathi("Reply with the single word: ok")

        return {
            "ok": True,
            "provider": "azure",
            "agent": "JanSathi",
            "version": "6",
            "detail": answer,
        }

    except Exception as exc:
        log.exception("Azure JanSaathi Agent ping failed.")

        return {
            "ok": False,
            "provider": "azure",
            "error": type(exc).__name__,
            "detail": str(exc)[:300],
        }


# ------------------------------------------------------------------
# Compatibility
# ------------------------------------------------------------------

def get_chat_response(
    message: str,
    language: str,
    history: list[ChatMessage],
    relevant_schemes: list[Scheme],
) -> str:

    hist = [
        {
            "role": h.role,
            "content": h.content,
        }
        for h in history
    ]

    ctx = ChatContext(
        message=message,
        language=language,
        history=hist,
        schemes=relevant_schemes,
        messages=prompts.build_messages(
            message,
            language,
            hist,
            relevant_schemes,
        ),
    )

    return generate_chat(ctx).text