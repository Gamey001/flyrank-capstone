"""The pipeline: plan -> write code -> run code -> format report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from app.agent import prompts
from app.agent.llm import get_chat_model
from app.dataset import describe
from app.envelope import ExecutionEnvelope
from app.observability import langsmith_reference
from app.queues import publish
from app.store import write_agent_record

DEFAULT_REQUEST = (
    "Build the quarterly order performance report for the customer."
)


class PipelineState(TypedDict, total=False):
    trace_id: str
    request: str
    scenario: str
    report_plan: dict
    source_prompt: str
    generated_code: str
    status: str


def stamped(config: RunnableConfig, trace_id: str, name: str) -> RunnableConfig:
    """Attach the trace ID to a model call."""
    cfg = dict(config or {})
    metadata = dict(cfg.get("metadata") or {})
    metadata["trace_id"] = trace_id
    tags = list(cfg.get("tags") or [])
    tags.append(f"trace:{trace_id}")
    cfg["metadata"] = metadata
    cfg["tags"] = tags
    cfg["run_name"] = name
    return cfg


def _strip_fences(text: str) -> str:
    """Models like to wrap code in markdown even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def plan_node(state: PipelineState, config: RunnableConfig) -> dict:
    schema = describe()
    messages = [
        SystemMessage(prompts.PLAN_SYSTEM),
        HumanMessage(
            prompts.PLAN_USER.format(
                request=state.get("request", DEFAULT_REQUEST),
                columns=", ".join(schema["columns"]),
                row_count=schema["row_count"],
            )
        ),
    ]
    raw = get_chat_model().invoke(
        messages, config=stamped(config, state["trace_id"], "plan_call")
    ).content
    return {"report_plan": json.loads(_strip_fences(str(raw))), "status": "planned"}


def write_code_node(state: PipelineState, config: RunnableConfig) -> dict:
    schema = describe()
    source_prompt = prompts.CODE_USER.format(
        plan=json.dumps(state["report_plan"], indent=2),
        columns=", ".join(schema["columns"]),
        scenario_note=prompts.scenario_note(state.get("scenario", "healthy")),
    )
    messages = [SystemMessage(prompts.CODE_SYSTEM), HumanMessage(source_prompt)]
    raw = get_chat_model().invoke(
        messages, config=stamped(config, state["trace_id"], "write_code_call")
    ).content
    return {
        "source_prompt": source_prompt,
        "generated_code": _strip_fences(str(raw)),
        "status": "code_written",
    }


def handoff_node(state: PipelineState) -> dict:
    """Package the run and put it on the waiting line."""
    envelope = ExecutionEnvelope(
        trace_id=state["trace_id"],
        generated_code=state["generated_code"],
        source_prompt=state["source_prompt"],
    )
    publish(envelope)

    write_agent_record(state["trace_id"], {
        "trace_id": state["trace_id"],
        "watcher": "in-process (agent + langsmith)",
        "status": "handed_off",
        "claim": "run finished successfully from inside the agent process",
        "report_plan": state["report_plan"],
        "source_prompt": state["source_prompt"],
        "generated_code": state["generated_code"],
        "scenario": state.get("scenario", "healthy"),
        "langsmith": langsmith_reference(state["trace_id"]),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "handed_off"}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("plan", plan_node)
    graph.add_node("write_code", write_code_node)
    graph.add_node("handoff", handoff_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "write_code")
    graph.add_edge("write_code", "handoff")
    graph.add_edge("handoff", END)
    return graph.compile()


PIPELINE = build_graph()


def run_pipeline(
    trace_id: str,
    request: str = DEFAULT_REQUEST,
    scenario: str = "healthy",
) -> PipelineState:
    """Run the pipeline under an ID that was minted elsewhere."""
    return PIPELINE.invoke(
        {
            "trace_id": trace_id,
            "request": request,
            "scenario": scenario,
            "status": "started",
        },
        config={
            "run_name": f"report-run {trace_id}",
            "metadata": {"trace_id": trace_id},
            "tags": [f"trace:{trace_id}"],
        },
    )
