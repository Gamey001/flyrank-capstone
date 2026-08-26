"""What an exit code means."""

from __future__ import annotations

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
