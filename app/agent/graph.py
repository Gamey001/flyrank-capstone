"""The pipeline: plan -> write code -> run code -> format report."""

from __future__ import annotations

import json
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.agent import prompts
from app.agent.llm import get_chat_model
from app.agent.runner import run_locally
from app.dataset import describe

DEFAULT_REQUEST = (
    "Build the quarterly order performance report for the customer."
)


class PipelineState(TypedDict, total=False):
    request: str
    report_plan: dict
    source_prompt: str
    generated_code: str
    execution: dict
    report: str
    status: str
    error: Optional[str]


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


def plan_node(state: PipelineState) -> dict:
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
    raw = get_chat_model().invoke(messages).content
    return {"report_plan": json.loads(_strip_fences(str(raw))), "status": "planned"}


def write_code_node(state: PipelineState) -> dict:
    schema = describe()
    source_prompt = prompts.CODE_USER.format(
        plan=json.dumps(state["report_plan"], indent=2),
        columns=", ".join(schema["columns"]),
    )
    messages = [SystemMessage(prompts.CODE_SYSTEM), HumanMessage(source_prompt)]
    raw = get_chat_model().invoke(messages).content
    return {
        "source_prompt": source_prompt,
        "generated_code": _strip_fences(str(raw)),
        "status": "code_written",
    }


def run_code_node(state: PipelineState) -> dict:
    result = run_locally(state["generated_code"])
    return {"execution": result.as_dict(), "status": "executed"}


def format_report_node(state: PipelineState) -> dict:
    execution = state["execution"]
    if not execution["ok"]:
        return {
            "status": "failed",
            "error": execution["stderr"].strip() or "execution failed",
            "report": "",
        }
    try:
        data: dict[str, Any] = json.loads(execution["stdout"])
    except json.JSONDecodeError as exc:
        return {
            "status": "failed",
            "error": f"script output was not JSON: {exc}",
            "report": "",
        }
    return {"status": "succeeded", "error": None, "report": render(state["report_plan"], data)}


def render(plan: dict, data: dict) -> str:
    lines = [f"# {plan.get('title', 'Report')}", ""]
    for section in plan.get("sections", []):
        name = section["name"]
        lines.append(f"## {name.replace('_', ' ').title()}")
        lines.append(f"*{section.get('question', '')}*")
        lines.append("")
        value = data.get(name)
        if isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
        elif value is None:
            lines.append("_no data returned for this section_")
        else:
            lines.append(f"- {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("plan", plan_node)
    graph.add_node("write_code", write_code_node)
    graph.add_node("run_code", run_code_node)
    graph.add_node("format_report", format_report_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "write_code")
    graph.add_edge("write_code", "run_code")
    graph.add_edge("run_code", "format_report")
    graph.add_edge("format_report", END)
    return graph.compile()


PIPELINE = build_graph()


def run_pipeline(request: str = DEFAULT_REQUEST) -> PipelineState:
    return PIPELINE.invoke({"request": request, "status": "started"})
