"""The host observer's loop."""

from __future__ import annotations

import signal
import sys
import time

from app import store
from app.envelope import ExecutionEnvelope
from app.queues import QUEUE_KEY, get_redis
from app.worker.host_observer import observe

_running = True


def _stop(signum, frame):
    global _running
    _running = False


def log(message: str) -> None:
    print(f"[host-observer] {message}", flush=True)


def main() -> int:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    client = get_redis()
    log(f"watching {QUEUE_KEY}")

    while _running:
        item = client.brpop(QUEUE_KEY, timeout=2)
        if item is None:
            continue

        envelope = ExecutionEnvelope.from_json(item[1])
        log(f"{envelope.trace_id} starting container")

        outcome = observe(envelope)

        store.write_outcome(outcome, client=client)
        client.lpush(store.RESULT_CHANNEL.format(envelope.trace_id), "done")
        client.expire(store.RESULT_CHANNEL.format(envelope.trace_id), 300)

        log(
            f"{envelope.trace_id} exit={outcome.exit_code} "
            f"verdict={outcome.verdict} ({outcome.duration_ms}ms)"
        )

    log("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
