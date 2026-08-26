#!/usr/bin/env python3
"""Submit one run and wait for the host observer's verdict."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "http://localhost:8000"


def _call(url: str, body: dict = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="healthy",
                        choices=["healthy", "oom", "segfault"])
    parser.add_argument("--request", default=None)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    body = {"scenario": args.scenario}
    if args.request:
        body["request"] = args.request

    submitted = _call(f"{args.base}/runs", body)
    trace_id = submitted["trace_id"]
    print(f"trace_id: {trace_id}", file=sys.stderr)
    print(f"agent:    {submitted['status']}", file=sys.stderr)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        run = _call(f"{args.base}/runs/{trace_id}")
        host = run.get("host_observer") or {}
        if not host.get("known"):
            time.sleep(0.5)
            continue

        print(
            f"host:     exit={host['exit_code']} verdict={host['verdict']} "
            f"({host['duration_ms']}ms)",
            file=sys.stderr,
        )
        print(f"          {host['says']}", file=sys.stderr)

        clash = run.get("disagreement") or {}
        if clash.get("present"):
            print(f"\ndisagreement: {clash['summary']}", file=sys.stderr)

        if run.get("report"):
            print(run["report"])
            return 0
        if host.get("stderr", "").strip():
            print(host["stderr"].strip()[-1500:], file=sys.stderr)
        return 0 if host.get("ok") else 1

    print("no outcome recorded — is the host observer running? (make worker)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
