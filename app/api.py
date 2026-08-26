"""FastAPI entry point."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app import __version__, store
from app.agent.graph import DEFAULT_REQUEST, run_pipeline
from app.agent.prompts import SCENARIO_NOTES
from app.config import settings
from app.observability import configure_langsmith
from app.queues import depth, peek
from app.reconcile import reconcile
from app.report import render
from app.trace_page import render_page
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


def _view(trace_id: str) -> tuple:
    """The joined view for one ID, plus the report if there is one."""
    view = reconcile(trace_id)
    if not view["inside_watcher"].get("known") and not view["host_observer"].get("known"):
        raise HTTPException(status_code=404, detail=f"no run for {trace_id}")

    report = None
    host = view["host_observer"]
    if host.get("ok"):
        try:
            report = render(
                view["inside_watcher"]["report_plan"], json.loads(host["stdout"])
            )
        except (KeyError, TypeError, json.JSONDecodeError):
            report = None
    return view, report


@app.get("/runs/{trace_id}")
def get_run(trace_id: str) -> dict:
    """Paste one ID: both views, and the disagreement between them."""
    view, report = _view(trace_id)
    view["report"] = report
    return view


@app.get("/trace/{trace_id}", response_class=HTMLResponse)
def trace_page(trace_id: str) -> str:
    """The same thing, side by side, for a human."""
    view, report = _view(trace_id)
    return render_page(view, report)


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
