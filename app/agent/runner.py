"""Phase 1 code runner — the "before" state, kept on purpose."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import asdict, dataclass

from app.config import settings
from app.dataset import DATA_PATH


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ok"] = self.ok
        return d


def run_locally(code: str) -> ExecutionResult:
    env = {"FLYRANK_DATA": str(DATA_PATH), "PATH": "/usr/bin:/bin"}
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=settings.sandbox_timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            exit_code=-1, stdout="", stderr="timed out", timed_out=True
        )
    return ExecutionResult(
        exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr
    )
