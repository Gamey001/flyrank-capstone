"""The outside watcher."""

from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone

from app.config import settings
from app.envelope import ExecutionEnvelope
from app.outcome import Outcome, classify


def docker_command(trace_id: str) -> list:
    """The terms the host sets for the sealed box."""
    return [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", settings.sandbox_memory_limit,
        "--memory-swap", settings.sandbox_memory_limit,
        "--pids-limit", "128",
        "--read-only",
        "--tmpfs", "/tmp:rw,size=16m",
        "-e", f"FLYRANK_TRACE_ID={trace_id}",
        "-e", "FLYRANK_DATA=/data/orders.csv",
        settings.sandbox_image,
    ]


def observe(envelope: ExecutionEnvelope) -> Outcome:
    """Run one envelope in a container and record what the host saw."""
    started = time.monotonic()
    timed_out = False

    try:
        proc = subprocess.run(
            docker_command(envelope.trace_id),
            input=envelope.generated_code,
            capture_output=True,
            text=True,
            timeout=settings.sandbox_timeout_seconds,
        )
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = -1
        stdout = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

    verdict, explanation = classify(exit_code, timed_out)

    return Outcome(
        trace_id=envelope.trace_id,
        exit_code=exit_code,
        verdict=verdict,
        explanation=explanation,
        stdout=stdout,
        stderr=stderr,
        duration_ms=int((time.monotonic() - started) * 1000),
        observed_at=datetime.now(timezone.utc).isoformat(),
        source_prompt=envelope.source_prompt,
        generated_code=envelope.generated_code,
        timed_out=timed_out,
    )
