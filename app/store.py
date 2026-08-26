"""Where run records live, keyed by trace ID."""

from __future__ import annotations

import json
from typing import Optional

from app.outcome import Outcome
from app.queues import get_redis

AGENT_KEY = "flyrank:agent:{}"
OUTCOME_KEY = "flyrank:outcome:{}"
RESULT_CHANNEL = "flyrank:result:{}"
QUARANTINE_SET = "flyrank:quarantine"
QUARANTINE_KEY = "flyrank:quarantine:{}"
REPLAYS_KEY = "flyrank:replays:{}"
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


def quarantine(trace_id: str, reason: str, detail: dict = None, client=None) -> None:
    """Hold a run back. Nothing about it ships."""
    r = client or get_redis()
    r.sadd(QUARANTINE_SET, trace_id)
    r.set(
        QUARANTINE_KEY.format(trace_id),
        json.dumps({"trace_id": trace_id, "reason": reason, "detail": detail or {}}),
        ex=TTL_SECONDS,
    )


def read_quarantine(trace_id: str, client=None) -> Optional[dict]:
    raw = (client or get_redis()).get(QUARANTINE_KEY.format(trace_id))
    return json.loads(raw) if raw else None


def list_quarantined(client=None) -> list:
    return sorted((client or get_redis()).smembers(QUARANTINE_SET))


def link_replay(original_id: str, replay_id: str, client=None) -> None:
    r = client or get_redis()
    r.rpush(REPLAYS_KEY.format(original_id), replay_id)
    r.expire(REPLAYS_KEY.format(original_id), TTL_SECONDS)


def list_replays(original_id: str, client=None) -> list:
    return (client or get_redis()).lrange(REPLAYS_KEY.format(original_id), 0, -1)
