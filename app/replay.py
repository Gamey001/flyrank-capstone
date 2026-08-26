"""Replaying a failing run from its trace ID alone."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app import store
from app.envelope import ExecutionEnvelope
from app.queues import publish
from app.trace import new_trace_id


def replay(trace_id: str) -> Optional[dict]:
    """Re-run a recorded run. Returns None if that ID has no outcome."""
    original = store.read_outcome(trace_id)
    if original is None:
        return None

    replay_id = new_trace_id()
    envelope = ExecutionEnvelope(
        trace_id=replay_id,
        generated_code=original.generated_code,
        source_prompt=original.source_prompt,
    )

    borrowed = store.read_agent_record(trace_id) or {}
    store.write_agent_record(replay_id, {
        "trace_id": replay_id,
        "watcher": "in-process (replay — no model call)",
        "status": "handed_off",
        "claim": "replayed from a recorded envelope",
        "replay_of": trace_id,
        "report_plan": borrowed.get("report_plan"),
        "source_prompt": original.source_prompt,
        "generated_code": original.generated_code,
        "scenario": borrowed.get("scenario"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })

    publish(envelope)
    store.link_replay(trace_id, replay_id)

    return {
        "replay_of": trace_id,
        "trace_id": replay_id,
        "original_exit_code": original.exit_code,
        "original_verdict": original.verdict,
    }


def compare(original_id: str, replay_id: str) -> dict:
    """Did the replay reproduce the failure?"""
    original = store.read_outcome(original_id)
    repeated = store.read_outcome(replay_id)
    if original is None or repeated is None:
        return {"complete": False, "reason": "one of the two runs has no outcome yet"}

    reproduced = original.exit_code == repeated.exit_code
    return {
        "complete": True,
        "reproduced": reproduced,
        "original": {"trace_id": original_id, "exit_code": original.exit_code,
                     "verdict": original.verdict},
        "replay": {"trace_id": replay_id, "exit_code": repeated.exit_code,
                   "verdict": repeated.verdict},
        "summary": (
            f"replay reproduced exit {original.exit_code}"
            if reproduced
            else f"replay exited {repeated.exit_code}, original exited "
                 f"{original.exit_code} — not reproduced"
        ),
    }
