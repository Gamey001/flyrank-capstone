"""The execution envelope — what crosses the queue boundary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

FIELDS = ("trace_id", "generated_code", "source_prompt")


@dataclass(frozen=True)
class ExecutionEnvelope:
    trace_id: str
    generated_code: str
    source_prompt: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "ExecutionEnvelope":
        data = json.loads(raw)
        missing = [f for f in FIELDS if f not in data]
        if missing:
            raise ValueError(f"envelope missing fields: {', '.join(missing)}")
        extra = [k for k in data if k not in FIELDS]
        if extra:
            raise ValueError(f"envelope has unexpected fields: {', '.join(extra)}")
        return cls(**data)
