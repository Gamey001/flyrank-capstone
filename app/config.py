"""Configuration, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load .env if python-dotenv is available; ignore it if not."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env")


_load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "flyrank-capstone"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    redis_url: str = "redis://localhost:6379/0"

    sandbox_image: str = "flyrank-sandbox:latest"
    sandbox_memory_limit: str = "128m"
    sandbox_timeout_seconds: int = 60

    @property
    def llm_is_live(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def langsmith_is_live(self) -> bool:
        return self.langsmith_tracing and bool(self.langsmith_api_key)


def load_settings() -> Settings:
    return Settings(
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_model=_env("OPENAI_MODEL", "gpt-4o-mini"),
        langsmith_tracing=_env("LANGSMITH_TRACING", "false").lower()
        in ("1", "true", "yes"),
        langsmith_api_key=_env("LANGSMITH_API_KEY"),
        langsmith_project=_env("LANGSMITH_PROJECT", "flyrank-capstone"),
        langsmith_endpoint=_env(
            "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
        ),
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        sandbox_image=_env("SANDBOX_IMAGE", "flyrank-sandbox:latest"),
        sandbox_memory_limit=_env("SANDBOX_MEMORY_LIMIT", "128m"),
        sandbox_timeout_seconds=int(_env("SANDBOX_TIMEOUT_SECONDS", "60")),
    )


settings = load_settings()
