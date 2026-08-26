"""Putting the two watchers side by side."""

from __future__ import annotations

from typing import Optional

from app import langsmith_view, store
from app.outcome import COMPLETED, Outcome


def _inside_view(trace_id: str) -> dict:
    """What the inside watcher believes happened."""
    agent = store.read_agent_record(trace_id)
    langsmith = langsmith_view.lookup(trace_id)

    if agent is None and not langsmith.get("found"):
        return {"known": False, "langsmith": langsmith}

    finished = bool(agent) and agent.get("status") == "handed_off"
    if langsmith.get("found"):
        finished = langsmith.get("status") == "success" and langsmith.get("closed")

    return {
        "known": True,
        "watcher": "in-process (agent + langsmith)",
        "verdict": "finished" if finished else "did not finish",
        "says": (
            "the run finished"
            if finished
            else "the run did not finish cleanly"
        ),
        "langsmith": langsmith,
        "report_plan": (agent or {}).get("report_plan"),
        "scenario": (agent or {}).get("scenario"),
        "recorded_at": (agent or {}).get("recorded_at"),
    }


def _host_view(outcome: Optional[Outcome]) -> dict:
    if outcome is None:
        return {
            "known": False,
            "says": "no outcome recorded — is the host observer running?",
        }
    return {
        "known": True,
        "watcher": "host (outside the container)",
        "verdict": outcome.verdict,
        "exit_code": outcome.exit_code,
        "says": outcome.explanation,
        "duration_ms": outcome.duration_ms,
        "quality": outcome.quality,
        "shippable": outcome.shippable,
        "observed_at": outcome.observed_at,
        "stdout": outcome.stdout,
        "stderr": outcome.stderr,
        "source_prompt": outcome.source_prompt,
        "generated_code": outcome.generated_code,
        "ok": outcome.ok,
    }


def reconcile(trace_id: str) -> dict:
    """Join both views for one ID and say plainly whether they agree."""
    outcome = store.read_outcome(trace_id)
    inside = _inside_view(trace_id)
    host = _host_view(outcome)

    disagreement = None
    if inside.get("known") and host.get("known"):
        inside_says_fine = inside["verdict"] == "finished"
        host_says_dead = outcome is not None and outcome.verdict != COMPLETED
        if inside_says_fine and host_says_dead:
            disagreement = {
                "present": True,
                "summary": (
                    f"the inside watcher says the run finished; the host says "
                    f"exit {outcome.exit_code} — {outcome.explanation.lower()}"
                ),
                "why": (
                    "The inside watcher is not wrong about what it saw. It saw the "
                    "agent plan, write the code and hand it off, and all of that "
                    "worked. The failure happened afterwards, in another process, "
                    "inside a container — somewhere it was never present to watch. "
                    "The host was, because the host is one level up."
                ),
                "authoritative": "host",
            }
        else:
            disagreement = {"present": False, "summary": "both watchers agree"}

    if (
        disagreement is not None
        and not disagreement["present"]
        and outcome is not None
        and outcome.ok
        and not outcome.shippable
    ):
        disagreement = {
            "present": True,
            "summary": (
                "both watchers say the run finished — and it did. It exited 0 "
                "and produced nothing usable."
            ),
            "why": (
                "This is the swallowed error. The script caught its own failure, "
                "shipped an empty report and exited cleanly, so every watcher "
                "that looks at the process sees success. Only something that "
                "reads what the run actually produced can tell, which is why "
                "the gate runs on the host after the container is gone."
            ),
            "authoritative": "host",
        }

    return {
        "trace_id": trace_id,
        "inside_watcher": inside,
        "host_observer": host,
        "disagreement": disagreement,
        "quarantine": store.read_quarantine(trace_id),
        "replays": store.list_replays(trace_id),
        "replay_of": (store.read_agent_record(trace_id) or {}).get("replay_of"),
    }
