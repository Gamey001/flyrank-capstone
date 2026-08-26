#!/usr/bin/env python3
"""Paste one trace ID, see both watchers."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import urllib.error
import urllib.request

RULE = "─" * 72


def _wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, width=72, initial_indent=indent,
                         subsequent_indent=indent)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_id")
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--code", action="store_true",
                        help="print the script that ran")
    args = parser.parse_args()

    try:
        with urllib.request.urlopen(
            f"{args.base}/runs/{args.trace_id}", timeout=30
        ) as response:
            view = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"no run for {args.trace_id}", file=sys.stderr)
            return 1
        raise

    inside = view["inside_watcher"]
    host = view["host_observer"]

    print(RULE)
    print(f"trace {view['trace_id']}")
    print(RULE)

    print("\nLangSmith  (inside the process)")
    if inside.get("known"):
        langsmith = inside.get("langsmith", {})
        print(f"  verdict : {inside['verdict']}")
        print(f"  status  : {langsmith.get('status') or langsmith.get('reason')}")
        print(f"  error   : {langsmith.get('error') or 'none'}")
    else:
        print("  nothing recorded")

    print("\nHost observer  (outside the container)")
    if host.get("known"):
        print(f"  verdict : {host['verdict']}")
        print(f"  exit    : {host['exit_code']}")
        print(f"  means   : {host['says']}")
        print(f"  took    : {host['duration_ms']}ms")
    else:
        print(f"  {host.get('says')}")

    held = view.get("quarantine")
    if held:
        print(f"\nQUARANTINED  reason: {held.get('reason')}")
        print("  nothing from this run ships")
    if view.get("replay_of"):
        print(f"\nthis run is a replay of {view['replay_of']}")
    if view.get("replays"):
        print(f"\nreplays of this run: {', '.join(view['replays'])}")

    clash = view.get("disagreement") or {}
    print()
    print(RULE)
    if clash.get("present"):
        print("THE WATCHERS DISAGREE")
        print(_wrap(clash["summary"]))
        print()
        print(_wrap(clash["why"]))
        print()
        print(f"  authoritative: {clash['authoritative']}")
    elif clash:
        print(clash["summary"])
    else:
        print("only one watcher has reported so far")
    print(RULE)

    if args.code and host.get("generated_code"):
        print("\nthe exact script that ran:\n")
        print(textwrap.indent(host["generated_code"], "  "))
        print("\nthe prompt that produced it:\n")
        print(textwrap.indent(host.get("source_prompt", ""), "  "))

    if view.get("report"):
        print("\n" + view["report"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
