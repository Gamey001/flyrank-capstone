# Observable LLM agent pipeline

**One trace ID that survives the crash LangSmith cannot see — because the
authoritative watcher sits on the host, outside the process that dies.**

A portfolio capstone. The pipeline is an AI agent that builds a customer report
by writing a small piece of code and then running it: real content as the
deliverable, real code execution as the thing that can fail hard.

## What this proves

I can take a messy, multi-step AI agent pipeline and make any single run fully
traceable — so that when a run fails, one trace ID links the failure straight
back to the exact step, prompt, model call, and inputs that caused it, *even
when the failure is the kind that normally leaves no trace at all*.

## The core principle

> **The thing that watches for failure cannot be the thing that might die.**

A step that crashes can't be trusted to report its own crash, so the reliable
watcher has to sit outside the thing it is watching.

Imagine a smoke alarm wired to the same power as the stove. The stove catches
fire, the fire cuts the power, the alarm goes dead — and stays silent. You
needed the one thing that couldn't survive the event to warn you about the
event.

That is the trap most pipeline monitoring falls into: the code that reports the
failure runs inside the process that failed, so when the process dies hard the
report never gets sent, and the dashboard stays green. This build puts the alarm
on its own power supply. The authoritative watcher lives one level up, on the
host, where it can still speak after the thing it was watching is gone.

This is why `docker-compose.yml` does not contain the observer.

## Why not just turn on LangSmith

LangSmith is genuinely useful and it is kept, not rebuilt — it gives the rich
view of every model call. But it watches from *inside* the running process, and
a record that opens when a step starts only closes when the step returns. Three
failures break that:

| Failure | What an inside-the-process watcher sees |
| --- | --- |
| Hard kill (`137` out-of-memory, `139` crash) | Nothing, or a record stuck half-open. The closing line never runs. |
| Swallowed error | A green, successful record. It lies. |
| Death across a process boundary | The watcher isn't present in the helper that died. |

## Stack

LangGraph · LangChain · LangSmith · FastAPI · Redis · Docker

## Status

**Phase 1 — working pipeline, happy path (`v0.2-pipeline`).** The LangGraph
agent runs end to end on a good run and produces a real report. LangSmith shows
the steps. There is no trace spine yet — that is Phase 2.

```bash
cp .env.example .env      # fill in keys; both are optional
make up
make health
make run                  # plan -> write code -> run code -> format report
```

The four steps are distinct nodes on purpose: a reviewer should be able to point
at the step that failed, and a single do-everything node would make the trace
useless.

`GET /health` reports whether the LLM and LangSmith are live. Neither is
required: with no `OPENAI_API_KEY` the agent runs on a deterministic offline
model — a real LangChain chat model going through the same graph, prompts and
callbacks — so every phase, including the crash demo, works with no credentials.

### The code runner is deliberately naive right now

Phase 1 runs the generated script as a child of the agent process and believes
what it sees. That is the "before" state this capstone argues against, and
`app/agent/runner.py` says so in full. Phase 3 replaces it with the host
observer.

Built on `dev`, one milestone tag per phase.
