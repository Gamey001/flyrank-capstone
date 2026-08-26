#!/usr/bin/env python3
"""Run the pipeline once and print the report."""

from __future__ import annotations

import sys

from app.agent.graph import DEFAULT_REQUEST, run_pipeline
from app.observability import configure_langsmith
from app.trace import new_trace_id


def main() -> int:
    live = configure_langsmith()
    print(f"langsmith: {'live' if live else 'off'}", file=sys.stderr)

    request = " ".join(sys.argv[1:]) or DEFAULT_REQUEST
    trace_id = new_trace_id()
    print(f"trace_id: {trace_id}", file=sys.stderr)
    state = run_pipeline(trace_id, request)

    print(f"status: {state['status']}", file=sys.stderr)
    if state["status"] != "succeeded":
        print(f"error: {state.get('error')}", file=sys.stderr)
        print(state.get("execution", {}).get("stderr", ""), file=sys.stderr)
        return 1
    print(state["report"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
