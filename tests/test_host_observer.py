"""The test that defines the boundary."""

from __future__ import annotations

import shutil
import subprocess
import uuid

import pytest

from app.envelope import ExecutionEnvelope
from app.outcome import (
    COMPLETED,
    HARD_CRASH,
    KILLED_OUT_OF_MEMORY,
    SCRIPT_ERROR,
    TIMED_OUT,
    classify,
)
from app.worker.host_observer import docker_command, observe

OOM_CODE = """\
chunks = []
while True:
    block = bytearray(8 * 1024 * 1024)
    block[::4096] = b"x" * len(block[::4096])
    chunks.append(block)
"""

LYING_CODE = """\
import sys
# The script announces success, then dies anyway. A watcher that believed the
# process about itself would file this as a clean run.
print('{"status": "ok", "rows": 1301}', flush=True)

chunks = []
while True:
    block = bytearray(8 * 1024 * 1024)
    block[::4096] = b"x" * len(block[::4096])
    chunks.append(block)
"""

HEALTHY_CODE = """\
import csv, json, os
rows = list(csv.DictReader(open(os.environ["FLYRANK_DATA"])))
print(json.dumps({"total_orders": len(rows)}))
"""


def _sandbox_available() -> bool:
    if shutil.which("docker") is None:
        return False
    probe = subprocess.run(
        ["docker", "image", "inspect", "flyrank-sandbox:latest"],
        capture_output=True,
    )
    return probe.returncode == 0


needs_sandbox = pytest.mark.skipif(
    not _sandbox_available(),
    reason="needs docker and flyrank-sandbox:latest (make sandbox)",
)


def _envelope(code: str) -> ExecutionEnvelope:
    return ExecutionEnvelope(
        trace_id=str(uuid.uuid4()),
        generated_code=code,
        source_prompt="test prompt",
    )


def test_exit_codes_map_to_verdicts():
    assert classify(0)[0] == COMPLETED
    assert classify(1)[0] == SCRIPT_ERROR
    assert classify(137)[0] == KILLED_OUT_OF_MEMORY
    assert classify(139)[0] == HARD_CRASH
    assert classify(0, timed_out=True)[0] == TIMED_OUT


def test_signal_deaths_are_not_silently_called_success():
    verdict, explanation = classify(143)
    assert verdict == HARD_CRASH
    assert "15" in explanation


def test_container_is_told_its_trace_id():
    command = docker_command("abc-123")
    assert "FLYRANK_TRACE_ID=abc-123" in command
    assert "none" in command


def test_memory_ceiling_disables_swap():
    """Without this the kernel swaps instead of killing, and there is no 137."""
    command = docker_command("abc-123")
    memory = command[command.index("--memory") + 1]
    swap = command[command.index("--memory-swap") + 1]
    assert memory == swap


@needs_sandbox
def test_a_memory_kill_is_recorded_by_the_host():
    envelope = _envelope(OOM_CODE)

    outcome = observe(envelope)

    assert outcome.exit_code == 137
    assert outcome.verdict == KILLED_OUT_OF_MEMORY
    assert outcome.ok is False
    assert outcome.trace_id == envelope.trace_id
    assert outcome.observer == "host"
    assert outcome.generated_code == OOM_CODE
    assert outcome.source_prompt == "test prompt"


@needs_sandbox
def test_the_containers_self_report_does_not_decide_the_verdict():
    """The box does not get to grade its own work."""
    outcome = observe(_envelope(LYING_CODE))

    assert '"status": "ok"' in outcome.stdout
    assert outcome.exit_code == 137
    assert outcome.verdict == KILLED_OUT_OF_MEMORY
    assert outcome.ok is False


@needs_sandbox
def test_a_good_run_still_completes():
    outcome = observe(_envelope(HEALTHY_CODE))

    assert outcome.exit_code == 0
    assert outcome.verdict == COMPLETED
    assert outcome.ok is True
    assert "total_orders" in outcome.stdout
