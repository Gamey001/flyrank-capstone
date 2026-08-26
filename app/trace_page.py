"""The paste-one-ID page."""

from __future__ import annotations

import html
import json

_STYLE = """
:root { color-scheme: light dark; --bg:#fbfbf9; --fg:#1b2a4a; --muted:#5b6b8c;
        --card:#ffffff; --line:#e2e5ec; --bad:#b23c2f; --good:#2f7a4d;
        --code:#f4f5f7; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#1b2a4a; --fg:#eef1f7; --muted:#a8b4cc; --card:#22335a;
          --line:#33456e; --bad:#f08a7c; --good:#7fd3a0; --code:#182644; }
}
* { box-sizing:border-box; }
body { margin:0; padding:2rem 1.25rem 4rem; background:var(--bg); color:var(--fg);
       font:15px/1.6 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif; }
.wrap { max-width:1080px; margin:0 auto; }
h1 { font-size:1.35rem; margin:0 0 .25rem; }
.id { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted);
      font-size:.9rem; word-break:break-all; }
.banner { margin:1.5rem 0; padding:1rem 1.15rem; border-radius:10px;
          border:1px solid var(--line); background:var(--card); }
.banner.clash { border-left:4px solid var(--bad); }
.banner.agree { border-left:4px solid var(--good); }
.banner h2 { margin:0 0 .4rem; font-size:1rem; }
.banner p { margin:.4rem 0 0; color:var(--muted); }
.cols { display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:1.15rem; }
.card h3 { margin:0 0 .1rem; font-size:.95rem; }
.card .role { color:var(--muted); font-size:.82rem; margin-bottom:.9rem; }
.verdict { font-size:1.15rem; font-weight:600; margin:0 0 .35rem; }
.verdict.bad { color:var(--bad); } .verdict.good { color:var(--good); }
dl { margin:.9rem 0 0; display:grid; grid-template-columns:auto 1fr; gap:.3rem .8rem; }
dt { color:var(--muted); font-size:.82rem; }
dd { margin:0; font-size:.86rem; word-break:break-word; }
pre { background:var(--code); border:1px solid var(--line); border-radius:8px;
      padding:.8rem; overflow-x:auto; font-size:.8rem; margin:.6rem 0 0; }
details { margin-top:1rem; } summary { cursor:pointer; color:var(--muted); font-size:.86rem; }
.note { color:var(--muted); font-size:.85rem; margin-top:2rem; }
"""


def _e(value) -> str:
    return html.escape("" if value is None else str(value))


def _banner(disagreement: dict) -> str:
    if not disagreement:
        return (
            '<div class="banner"><h2>Waiting</h2>'
            "<p>Only one watcher has reported so far.</p></div>"
        )
    if disagreement.get("present"):
        return (
            '<div class="banner clash"><h2>The watchers disagree</h2>'
            f"<p>{_e(disagreement['summary'])}</p>"
            f"<p>{_e(disagreement['why'])}</p></div>"
        )
    return (
        '<div class="banner agree"><h2>Both watchers agree</h2>'
        f"<p>{_e(disagreement['summary'])}</p></div>"
    )


def _inside_card(inside: dict) -> str:
    if not inside.get("known"):
        return (
            '<div class="card"><h3>LangSmith</h3>'
            '<div class="role">inside the process</div>'
            "<p>Nothing recorded for this ID.</p></div>"
        )
    langsmith = inside.get("langsmith", {})
    rows = [
        ("says", inside.get("says")),
        ("langsmith status", langsmith.get("status") or langsmith.get("reason")),
        ("record closed", langsmith.get("closed")),
        ("error", langsmith.get("error") or "none"),
        ("scenario", inside.get("scenario")),
    ]
    good = inside.get("verdict") == "finished"
    return (
        '<div class="card"><h3>LangSmith</h3>'
        '<div class="role">inside the process</div>'
        f'<p class="verdict {"good" if good else "bad"}">{_e(inside.get("verdict"))}</p>'
        "<dl>"
        + "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>" for k, v in rows)
        + "</dl></div>"
    )


def _host_card(host: dict) -> str:
    if not host.get("known"):
        return (
            '<div class="card"><h3>Host observer</h3>'
            '<div class="role">outside the container</div>'
            f"<p>{_e(host.get('says'))}</p></div>"
        )
    rows = [
        ("exit code", host.get("exit_code")),
        ("means", host.get("says")),
        ("duration", f"{host.get('duration_ms')}ms"),
        ("observed at", host.get("observed_at")),
    ]
    body = (
        '<div class="card"><h3>Host observer</h3>'
        '<div class="role">outside the container</div>'
        f'<p class="verdict {"good" if host.get("ok") else "bad"}">'
        f'{_e(host.get("verdict"))}</p>'
        "<dl>"
        + "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>" for k, v in rows)
        + "</dl>"
    )
    if host.get("generated_code"):
        body += (
            "<details open><summary>the exact script that ran</summary>"
            f"<pre>{_e(host['generated_code'])}</pre></details>"
        )
    if host.get("source_prompt"):
        body += (
            "<details><summary>the prompt that produced it</summary>"
            f"<pre>{_e(host['source_prompt'])}</pre></details>"
        )
    if (host.get("stderr") or "").strip():
        body += (
            "<details><summary>stderr</summary>"
            f"<pre>{_e(host['stderr'][-4000:])}</pre></details>"
        )
    return body + "</div>"


def render_page(view: dict, report: str = None) -> str:
    trace_id = view["trace_id"]
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>trace {_e(trace_id)}</title><style>{_STYLE}</style></head><body>",
        "<div class='wrap'>",
        "<h1>One trace ID, two watchers</h1>",
        f"<div class='id'>{_e(trace_id)}</div>",
        _banner(view.get("disagreement")),
        "<div class='cols'>",
        _inside_card(view.get("inside_watcher", {})),
        _host_card(view.get("host_observer", {})),
        "</div>",
    ]
    if report:
        parts.append(
            "<details><summary>the report this run produced</summary>"
            f"<pre>{_e(report)}</pre></details>"
        )
    parts.append(
        "<p class='note'>The host observer's record is written on the host, "
        "after the container has fully exited, from the exit code the host "
        "collected. That is why it survives a kill the inside watcher cannot "
        "see.</p>"
    )
    parts.append("</div></body></html>")
    return "".join(parts)
