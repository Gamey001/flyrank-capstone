"""FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import __version__
from app.agent.graph import DEFAULT_REQUEST, run_pipeline
from app.config import settings
from app.observability import configure_langsmith
from app.queues import depth, peek
from app.trace import new_trace_id

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
    trace_id = new_trace_id()
    state = run_pipeline(trace_id, body.request)
    return {
        "trace_id": trace_id,
        "status": state["status"],
        "error": state.get("error"),
        "plan": state.get("report_plan"),
        "generated_code": state.get("generated_code"),
        "execution": state.get("execution"),
        "report": state.get("report"),
    }


@app.get("/queue")
def queue_state() -> dict:
    """What is sitting on the waiting line, by trace ID."""
    return {
        "depth": depth(),
        "waiting": [
            {"trace_id": e.trace_id, "code_bytes": len(e.generated_code)}
            for e in peek()
        ],
    }
