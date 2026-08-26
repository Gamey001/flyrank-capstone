"""Reading back what the inside watcher recorded."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from app.config import settings

_TIMEOUT = 20
_session_id: Optional[str] = None


def _request(path: str, body: Optional[dict] = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"x-api-key": settings.langsmith_api_key}
    if data:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        settings.langsmith_endpoint + path, data=data, headers=headers
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
        return json.loads(response.read())


def _project_id() -> Optional[str]:
    global _session_id
    if _session_id is None:
        sessions = _request(f"/api/v1/sessions?name={settings.langsmith_project}")
        if not sessions:
            return None
        _session_id = sessions[0]["id"]
    return _session_id


def lookup(trace_id: str) -> dict:
    """What LangSmith says about this run."""
    if not settings.langsmith_is_live:
        return {
            "available": False,
            "reason": "langsmith tracing is off",
        }

    try:
        project = _project_id()
        if project is None:
            return {
                "available": False,
                "reason": f"no langsmith project named {settings.langsmith_project!r}",
            }
        result = _request(
            "/api/v1/runs/query",
            {
                "session": [project],
                "filter": f'has(tags, "trace:{trace_id}")',
                "is_root": True,
                "limit": 1,
                "select": ["name", "status", "error", "start_time", "end_time"],
            },
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"available": False, "reason": f"langsmith unreachable: {exc}"}

    runs = result.get("runs", [])
    if not runs:
        return {"available": True, "found": False, "reason": "no run recorded yet"}

    run = runs[0]
    return {
        "available": True,
        "found": True,
        "name": run.get("name"),
        "status": run.get("status"),
        "error": run.get("error"),
        "ended_at": run.get("end_time"),
        "closed": run.get("end_time") is not None,
    }
