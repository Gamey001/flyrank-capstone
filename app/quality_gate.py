"""The drift / quality gate."""

from __future__ import annotations

import json


def evaluate(plan: dict, stdout: str) -> dict:
    """Check a completed run's output against the plan it was meant to fulfil."""
    checks = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        record("output_is_json", False, "the script's output was not JSON")
        return _result(checks)
    record("output_is_json", True, "parsed cleanly")

    if not isinstance(data, dict):
        record("output_is_an_object", False, f"got {type(data).__name__}")
        return _result(checks)

    sections = [s["name"] for s in (plan or {}).get("sections", [])]
    if not sections:
        record("plan_had_sections", False, "no plan to check against")
        return _result(checks)

    missing = [s for s in sections if s not in data]
    record(
        "every_planned_section_present",
        not missing,
        "all present" if not missing else f"missing: {', '.join(missing)}",
    )

    empty = [s for s in sections if s in data and not data[s]]
    record(
        "no_section_is_empty",
        not empty,
        "all populated" if not empty else f"empty: {', '.join(empty)}",
    )

    return _result(checks)


def _result(checks: list) -> dict:
    failed = [c for c in checks if not c["passed"]]
    return {
        "passed": not failed,
        "checks": checks,
        "failures": [c["detail"] for c in failed],
        "summary": (
            "the run produced what it planned to"
            if not failed
            else "exited 0 but did not produce the report it planned"
        ),
    }
