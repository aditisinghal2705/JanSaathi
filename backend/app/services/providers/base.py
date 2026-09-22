"""Shared types for chat providers."""
from dataclasses import dataclass, field
from typing import Iterator, Protocol

from app.models.schemas import Scheme


@dataclass
class ChatContext:
    """Everything a provider needs to answer one chat turn."""
    message: str                      # user message, already redacted
    language: str                     # "en" | "pa" | "hi"
    history: list[dict]               # recent turns, already redacted
    schemes: list[Scheme]             # records selected by search
    messages: list[dict] = field(default_factory=list)   # full prompt for LLM providers
    redacted: bool = False            # True if a private number was removed


class ChatProvider(Protocol):
    name: str

    def generate(self, ctx: ChatContext) -> str: ...

    def stream(self, ctx: ChatContext) -> Iterator[str]: ...
