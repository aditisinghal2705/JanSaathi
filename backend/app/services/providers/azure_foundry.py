"""
Azure AI Foundry provider.

Talks to a model *deployment* in your Foundry resource through the
OpenAI-compatible v1 endpoint:

    https://<resource>.openai.azure.com/openai/v1/

This works for models sold by Azure (GPT family, DeepSeek, Grok, Llama, ...) and
for your own fine-tuned deployments: whatever name you gave the deployment goes
into AZURE_OPENAI_DEPLOYMENT.

Authentication
    * API key:    set AZURE_OPENAI_API_KEY
    * Keyless:    leave the key empty. The app then uses DefaultAzureCredential
                  (az login on your laptop, managed identity once deployed).
                  Give the identity the "Cognitive Services OpenAI User" role
                  on the Foundry resource.

Reference: https://learn.microsoft.com/azure/ai-foundry/openai/api-version-lifecycle
"""
import logging
import time
from typing import Iterator

from app.config import Settings, settings as default_settings
from app.services.providers.base import ChatContext

log = logging.getLogger("jansaathi.azure")


class ProviderError(RuntimeError):
    pass


class AzureFoundryProvider:
    name = "azure"

    def __init__(self, cfg: Settings | None = None):
        self.cfg = cfg or default_settings
        self._client = None
        # Some model families reject certain parameters. We learn that on the
        # first 400 error and remember it, so later requests succeed first time.
        self._drop_temperature = False
        self._token_param: str | None = "max_completion_tokens"  # None = send no limit

    # ------------------------------------------------------------------ client
    def _get_client(self):
        if self._client is not None:
            return self._client

        # Imported here so local mode does not need the openai package at all.
        from openai import OpenAI

        if self.cfg.azure_api_key:
            api_key = self.cfg.azure_api_key
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            api_key = get_bearer_token_provider(DefaultAzureCredential(), self.cfg.azure_token_scope)

        self._client = OpenAI(
            base_url=self.cfg.azure_base_url,
            api_key=api_key,
            timeout=self.cfg.request_timeout,
            max_retries=2,
        )
        return self._client

    # ------------------------------------------------------------------ calls
    def _params(self, messages: list[dict], stream: bool) -> dict:
        params: dict = {
            "model": self.cfg.azure_deployment,  # deployment name, not base model name
            "messages": messages,
            "stream": stream,
        }
        if self._token_param:
            params[self._token_param] = self.cfg.model_max_tokens
        if self.cfg.model_temperature is not None and not self._drop_temperature:
            params["temperature"] = self.cfg.model_temperature
        return params

    def _create(self, messages: list[dict], stream: bool = False):
        client = self._get_client()
        last_error: Exception | None = None
        for _ in range(3):
            try:
                return client.chat.completions.create(**self._params(messages, stream))
            except Exception as exc:  # noqa: BLE001 - inspected below
                last_error = exc
                if not self._adapt_to_error(exc):
                    raise
        raise ProviderError(f"Azure request failed after adjusting parameters: {last_error}")

    def _adapt_to_error(self, exc: Exception) -> bool:
        """If a 400 says a parameter is unsupported, adjust and report True to retry."""
        if getattr(exc, "status_code", None) != 400:
            return False
        text = str(exc).lower()

        if "temperature" in text and not self._drop_temperature:
            log.warning("Model rejected 'temperature'; sending requests without it from now on.")
            self._drop_temperature = True
            return True

        if self._token_param and self._token_param in text:
            if self._token_param == "max_completion_tokens":
                log.warning("Model rejected 'max_completion_tokens'; switching to 'max_tokens'.")
                self._token_param = "max_tokens"
            else:
                log.warning("Model rejected 'max_tokens'; sending requests without a token limit.")
                self._token_param = None
            return True

        return False

    # -------------------------------------------------------------- interface
    def generate(self, ctx: ChatContext) -> str:
        response = self._create(ctx.messages, stream=False)
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError("Model returned an empty answer.")
        return text

    def stream(self, ctx: ChatContext) -> Iterator[str]:
        stream = self._create(ctx.messages, stream=True)
        produced = False
        for chunk in stream:
            # Azure sends a first chunk with prompt-filter results and no choices.
            if not getattr(chunk, "choices", None):
                continue
            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)
            piece = getattr(delta, "content", None) if delta else None
            if piece:
                produced = True
                yield piece
            if getattr(choice, "finish_reason", None) == "content_filter" and not produced:
                raise ProviderError("Response was blocked by the content filter.")
        if not produced:
            raise ProviderError("Model returned an empty answer.")

    def ping(self) -> dict:
        """Tiny live call used by GET /api/ai/status to verify the Azure wiring."""
        started = time.perf_counter()
        response = self._create(
            [{"role": "user", "content": "Reply with the single word: ok"}], stream=False
        )
        return {
            "ok": True,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "deployment": self.cfg.azure_deployment,
            "model": getattr(response, "model", None),
            "auth": self.cfg.azure_auth_mode,
        }

