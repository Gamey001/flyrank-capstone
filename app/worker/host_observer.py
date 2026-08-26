"""The outside watcher."""

from __future__ import annotations

import subprocess
import time
from app.config import settings
from app.envelope import ExecutionEnvelope


def docker_command() -> list:
    """The terms the host sets for the sealed box."""
    return [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", settings.sandbox_memory_limit,
        "--memory-swap", settings.sandbox_memory_limit,
        "--pids-limit", "128",
        "--read-only",
        "--tmpfs", "/tmp:rw,size=16m",
        "-e", "FLYRANK_DATA=/data/orders.csv",
        settings.sandbox_image,
    ]


def run_in_container(envelope: ExecutionEnvelope) -> tuple:
    """Run one envelope in a container and return what the host saw."""
    started = time.monotonic()
    timed_out = False

    try:
        proc = subprocess.run(
            docker_command(),
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

    duration_ms = int((time.monotonic() - started) * 1000)
    return exit_code, stdout, stderr, timed_out, duration_ms
