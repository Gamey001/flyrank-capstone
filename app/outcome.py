"""The authoritative outcome record."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional

COMPLETED = "completed"
SCRIPT_ERROR = "script_error"
KILLED_OUT_OF_MEMORY = "killed_out_of_memory"
HARD_CRASH = "hard_crash"
TIMED_OUT = "timed_out"
UNKNOWN = "unknown"

_EXIT_CODES = {
    0: (COMPLETED, "Clean finish. Everything worked."),
    1: (SCRIPT_ERROR, "The script errored out on its own."),
    137: (KILLED_OUT_OF_MEMORY, "Killed for using too much memory (out-of-memory)."),
    139: (HARD_CRASH, "Hard crash (segfault)."),
}


def classify(exit_code: int, timed_out: bool = False) -> tuple:
    """Turn an exit code into a verdict the host is willing to stand behind."""
    if timed_out:
        return TIMED_OUT, "The container outlived its deadline and was stopped."
    if exit_code in _EXIT_CODES:
        return _EXIT_CODES[exit_code]
    if exit_code > 128:
        signal = exit_code - 128
        return HARD_CRASH, f"Killed by signal {signal}."
    return UNKNOWN, f"Exited {exit_code}."


@dataclass
class Outcome:
    trace_id: str
    exit_code: int
    verdict: str
    explanation: str
    stdout: str
    stderr: str
    duration_ms: int
    observed_at: str
    source_prompt: str = ""
    generated_code: str = ""
    observer: str = "host"
    timed_out: bool = False
    quality: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Exited cleanly."""
        return self.verdict == COMPLETED

    @property
    def shippable(self) -> bool:
        """Exited cleanly *and* produced what it planned to."""
        if not self.ok:
            return False
        return self.quality.get("passed", True)

    def to_json(self) -> str:
        d = asdict(self)
        d["ok"] = self.ok
        d["shippable"] = self.shippable
        return json.dumps(d)

    @classmethod
    def from_json(cls, raw: str) -> "Outcome":
        data = json.loads(raw)
        data.pop("ok", None)
        data.pop("shippable", None)
        return cls(**data)
