"""The gate that catches a clean exit which shipped nothing."""

from __future__ import annotations

import json

from app.outcome import COMPLETED, KILLED_OUT_OF_MEMORY, Outcome
from app.quality_gate import evaluate

PLAN = {
    "title": "Q2 order performance",
    "sections": [
        {"name": "revenue_by_region", "question": "?"},
        {"name": "refund_rate", "question": "?"},
    ],
}

FULL_OUTPUT = json.dumps({
    "revenue_by_region": {"NA": 66545.07},
    "refund_rate": {"rate_pct": 3.61},
})


def _outcome(exit_code: int, verdict: str, stdout: str, quality=None) -> Outcome:
    return Outcome(
        trace_id="t", exit_code=exit_code, verdict=verdict,
        explanation="", stdout=stdout, stderr="", duration_ms=1,
        observed_at="now", quality=quality or {},
    )


def test_a_complete_report_passes():
    result = evaluate(PLAN, FULL_OUTPUT)

    assert result["passed"] is True
    assert result["failures"] == []


def test_an_empty_report_is_caught():
    result = evaluate(PLAN, json.dumps({}))

    assert result["passed"] is False
    assert any("revenue_by_region" in f for f in result["failures"])


def test_a_present_but_empty_section_is_caught():
    """The section is there and holds nothing. Structurally fine, useless."""
    result = evaluate(PLAN, json.dumps({"revenue_by_region": {}, "refund_rate": {}}))

    assert result["passed"] is False
    assert any("empty" in f for f in result["failures"])


def test_output_that_is_not_json_is_caught():
    result = evaluate(PLAN, "Traceback (most recent call last):")

    assert result["passed"] is False


def test_exiting_zero_is_not_enough_to_ship():
    """The whole point: a clean exit and an empty report is not a success."""
    failed_gate = evaluate(PLAN, json.dumps({}))
    outcome = _outcome(0, COMPLETED, json.dumps({}), quality=failed_gate)

    assert outcome.ok is True
    assert outcome.shippable is False


def test_a_good_run_ships():
    outcome = _outcome(0, COMPLETED, FULL_OUTPUT, quality=evaluate(PLAN, FULL_OUTPUT))

    assert outcome.ok is True
    assert outcome.shippable is True


def test_a_killed_run_never_ships():
    outcome = _outcome(137, KILLED_OUT_OF_MEMORY, "")

    assert outcome.ok is False
    assert outcome.shippable is False


def test_the_record_survives_a_round_trip():
    """The outcome is stored as JSON; the gate result has to come back intact."""
    original = _outcome(0, COMPLETED, json.dumps({}), quality=evaluate(PLAN, "{}"))

    restored = Outcome.from_json(original.to_json())

    assert restored.quality["passed"] is False
    assert restored.shippable is False
