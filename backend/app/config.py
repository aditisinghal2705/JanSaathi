"""
Central configuration for the JanSaathi API.

Everything comes from environment variables (loaded from backend/.env in
development). Nothing else in the codebase reads os.environ directly, so this
file is the single place to look when wiring up Azure.

AI_PROVIDER
    local  - built-in, retrieval-only answers. No keys, no network. This is the
             default so the whole site works before Azure is connected.
    azure  - Azure AI Foundry model deployment (see services/providers/azure_foundry.py)
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _opt_float(name: str, default: float | None) -> float | None:
    """Float env var where blank means 'do not send this parameter'."""
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return default


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def normalize_foundry_base_url(endpoint: str) -> str:
    """
    Turn whatever was pasted from the Azure / Foundry portal into the
    OpenAI-compatible base URL:  https://<resource>.openai.azure.com/openai/v1/

    Accepts:
      https://<resource>.openai.azure.com/
      https://<resource>.services.ai.azure.com/
      https://<resource>.services.ai.azure.com/api/projects/<project>
      https://<resource>.openai.azure.com/openai/v1/
    """
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return ""
    if "://" not in endpoint:
        endpoint = "https://" + endpoint
    parsed = urlparse(endpoint)
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/openai/v1/"


@dataclass
class Settings:
    # --- AI provider -------------------------------------------------------
    ai_provider: str = field(default_factory=lambda: _str("AI_PROVIDER", "local").lower())

    # Azure AI Foundry (model deployment, OpenAI-compatible v1 endpoint)
    azure_endpoint: str = field(default_factory=lambda: _str("AZURE_OPENAI_ENDPOINT"))
    azure_api_key: str = field(default_factory=lambda: _str("AZURE_OPENAI_API_KEY"))
    # NOTE: this is your *deployment name* in Foundry, not the base model name.
    azure_deployment: str = field(default_factory=lambda: _str("AZURE_OPENAI_DEPLOYMENT"))
    # Used only when no API key is set (Microsoft Entra ID / managed identity).
    azure_token_scope: str = field(
        default_factory=lambda: _str("AZURE_AI_TOKEN_SCOPE", "https://ai.azure.com/.default")
    )

    # Generation controls
    model_max_tokens: int = field(default_factory=lambda: _int("MODEL_MAX_TOKENS", 700))
    # Blank = do not send (required for reasoning models such as o-series / gpt-5).
    model_temperature: float | None = field(default_factory=lambda: _opt_float("MODEL_TEMPERATURE", 0.2))
    request_timeout: int = field(default_factory=lambda: _int("REQUEST_TIMEOUT_SECONDS", 30))

    # --- Request limits ----------------------------------------------------
    max_history_messages: int = field(default_factory=lambda: _int("MAX_HISTORY_MESSAGES", 10))
    rate_limit_per_minute: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_MINUTE", 30))
    # Set true when running behind Azure App Service / Container Apps / Front Door
    # so the real client IP is read from X-Forwarded-For.
    trust_proxy: bool = field(default_factory=lambda: _bool("TRUST_PROXY", False))

    # --- Web ---------------------------------------------------------------
    allowed_origins: list[str] = field(
        default_factory=lambda: _list("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    # If this folder exists (the built React app), FastAPI serves it at "/".
    static_dir: str = field(default_factory=lambda: _str("STATIC_DIR", str(BASE_DIR / "static")))
    log_level: str = field(default_factory=lambda: _str("LOG_LEVEL", "INFO").upper())

    # ---------------------------------------------------------------------
    @property
    def azure_base_url(self) -> str:
        return normalize_foundry_base_url(self.azure_endpoint)

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_base_url and self.azure_deployment)

    @property
    def azure_auth_mode(self) -> str:
        return "api_key" if self.azure_api_key else "entra_id"

    @property
    def effective_provider(self) -> str:
        """The provider that will actually answer chat requests."""
        if self.ai_provider == "azure" and self.azure_configured:
            return "azure"
        return "local"


settings = Settings()
