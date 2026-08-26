"""FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.config import settings

app = FastAPI(
    title="flyrank capstone",
    description="Observable LLM agent pipeline: one trace ID that survives the crash.",
    version=__version__,
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "llm": "live" if settings.llm_is_live else "offline-deterministic",
        "langsmith": "live" if settings.langsmith_is_live else "off",
    }
