import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from app.core.rate_limit import rate_limited
from app.models.schemas import ChatRequest, ChatResponse
from app.services import ai_service, chat_pipeline

log = logging.getLogger("jansaathi.chat")
router = APIRouter(prefix="/api/chat", tags=["chat"])


class CompatStreamingResponse(StreamingResponse):
    """Keep a sync body iterator for compatibility with tests and older integrations."""

    def __init__(self, content, status_code: int = 200, headers=None, media_type: str | None = None, background=None):
        self.body_iterator = content
        self.status_code = status_code
        self.media_type = self.media_type if media_type is None else media_type
        self.background = background
        self.init_headers(headers)

    async def stream_response(self, send):
        try:
            iterator = self.body_iterator
            for chunk in iterator:
                if not isinstance(chunk, (bytes, memoryview)):
                    chunk = chunk.encode(self.charset)
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        except TypeError:
            async for chunk in self.body_iterator:
                if not isinstance(chunk, (bytes, memoryview)):
                    chunk = chunk.encode(self.charset)
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        await send({"type": "http.response.body", "body": b"", "more_body": False})


def _require_text(payload: ChatRequest) -> None:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message is empty.")


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, _: None = Depends(rate_limited)):
    """Single JSON reply. Use /api/chat/stream for token-by-token output."""
    _require_text(payload)
    ctx = chat_pipeline.prepare(payload)
    result = ai_service.generate_chat(ctx)
    return ChatResponse(
        reply=result.text,
        matched_schemes=chat_pipeline.summarize(ctx.schemes, payload.language),
        suggestions=chat_pipeline.suggestions_for(ctx.schemes, payload.language),
        provider=result.provider,
        degraded=result.degraded,
    )


@router.post("/stream")
def chat_stream(payload: ChatRequest, _: None = Depends(rate_limited)):
    """
    Server-sent events. Each event is one line:  data: {json}\\n\\n

      {"type": "meta",  "matched_schemes": [...], "provider": "azure"}
      {"type": "delta", "text": "..."}                       (many)
      {"type": "done",  "suggestions": [...], "provider": "...", "degraded": false, "interrupted": false}
      {"type": "error"}                                      (only if something broke mid-stream)
    """
    _require_text(payload)
    ctx = chat_pipeline.prepare(payload)
    stream = ai_service.open_stream(ctx)
    matched = [s.model_dump() for s in chat_pipeline.summarize(ctx.schemes, payload.language)]
    suggestions = chat_pipeline.suggestions_for(ctx.schemes, payload.language)

    def events():
        yield _sse({"type": "meta", "matched_schemes": matched, "provider": stream.provider})
        try:
            for piece in stream:
                yield _sse({"type": "delta", "text": piece})
        except Exception:  # noqa: BLE001
            log.exception("Chat stream failed")
            yield _sse({"type": "error"})
            return
        yield _sse({
            "type": "done",
            "suggestions": suggestions,
            "provider": stream.provider,
            "degraded": stream.degraded,
            "interrupted": stream.interrupted,
        })

    return CompatStreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
