"""FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import __version__
from app.agent.graph import DEFAULT_REQUEST, run_pipeline
from app.config import settings
from app.observability import configure_langsmith

LANGSMITH_LIVE = configure_langsmith()

app = FastAPI(
    title="flyrank capstone",
    description="Observable LLM agent pipeline: one trace ID that survives the crash.",
    version=__version__,
)


class RunRequest(BaseModel):
    request: str = Field(default=DEFAULT_REQUEST)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "llm": "live" if settings.llm_is_live else "offline-deterministic",
        "langsmith": "live" if LANGSMITH_LIVE else "off",
    }


@app.post("/runs")
def create_run(body: RunRequest) -> dict:
    state = run_pipeline(body.request)
    return {
        "status": state["status"],
        "error": state.get("error"),
        "plan": state.get("report_plan"),
        "generated_code": state.get("generated_code"),
        "execution": state.get("execution"),
        "report": state.get("report"),
    }
