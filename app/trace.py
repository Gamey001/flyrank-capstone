"""The trace ID."""

from __future__ import annotations

import uuid


def new_trace_id() -> str:
    """Mint the one ID for a run. Called only from the API entry point."""
    return str(uuid.uuid4())
