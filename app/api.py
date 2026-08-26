"""FastAPI entry point."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import __version__, store
from app.agent.graph import DEFAULT_REQUEST, run_pipeline
from app.agent.prompts import SCENARIO_NOTES
from app.config import settings
from app.observability import configure_langsmith
from app.queues import depth, peek
from app.report import render
from app.trace import new_trace_id

LANGSMITH_LIVE = configure_langsmith()

app = FastAPI(
    title="flyrank capstone",
    description="Observable LLM agent pipeline: one trace ID that survives the crash.",
    version=__version__,
)


class RunRequest(BaseModel):
    request: str = Field(default=DEFAULT_REQUEST)
    scenario: str = Field(
        default="healthy",
        description="healthy | oom | segfault — which failure to provoke.",
    )


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
    """Entry. This is where the trace ID is born."""
    if body.scenario not in SCENARIO_NOTES:
        raise HTTPException(
            status_code=400,
            detail=f"unknown scenario; expected one of {', '.join(SCENARIO_NOTES)}",
        )

    trace_id = new_trace_id()
    state = run_pipeline(trace_id, body.request, body.scenario)
    return {
        "trace_id": trace_id,
        "status": state["status"],
        "scenario": body.scenario,
        "note": "the host observer records the outcome; poll GET /runs/{trace_id}",
    }


@app.get("/runs/{trace_id}")
def get_run(trace_id: str) -> dict:
    """Everything known about one ID, from both watchers."""
    agent = store.read_agent_record(trace_id)
    outcome = store.read_outcome(trace_id)
    if agent is None and outcome is None:
        raise HTTPException(status_code=404, detail=f"no run for {trace_id}")

    report = None
    if outcome is not None and outcome.ok:
        try:
            report = render(agent["report_plan"], json.loads(outcome.stdout))
        except (KeyError, TypeError, json.JSONDecodeError):
            report = None

    return {
        "trace_id": trace_id,
        "inside_watcher": agent,
        "host_observer": json.loads(outcome.to_json()) if outcome else None,
        "report": report,
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
