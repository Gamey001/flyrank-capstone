"""Where run records live, keyed by trace ID."""

from __future__ import annotations

import json
from typing import Optional

from app.outcome import Outcome
from app.queues import get_redis

AGENT_KEY = "flyrank:agent:{}"
OUTCOME_KEY = "flyrank:outcome:{}"
RESULT_CHANNEL = "flyrank:result:{}"
TTL_SECONDS = 60 * 60 * 24


def write_outcome(outcome: Outcome, client=None) -> None:
    r = client or get_redis()
    r.set(OUTCOME_KEY.format(outcome.trace_id), outcome.to_json(), ex=TTL_SECONDS)


def read_outcome(trace_id: str, client=None) -> Optional[Outcome]:
    raw = (client or get_redis()).get(OUTCOME_KEY.format(trace_id))
    return Outcome.from_json(raw) if raw else None


def write_agent_record(trace_id: str, record: dict, client=None) -> None:
    r = client or get_redis()
    r.set(AGENT_KEY.format(trace_id), json.dumps(record), ex=TTL_SECONDS)


def read_agent_record(trace_id: str, client=None) -> Optional[dict]:
    raw = (client or get_redis()).get(AGENT_KEY.format(trace_id))
    return json.loads(raw) if raw else None
