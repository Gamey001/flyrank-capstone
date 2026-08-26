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

## The demo

### Before

A run fails. The dashboard is green. To find out what happened you comb through
logs by hand across several services, guessing which of thousands of runs was
the bad one. In the incident this is based on, that took roughly fourteen hours.

### After

Paste one trace ID and get both views side by side:

```
$ python3 scripts/run.py --scenario oom
trace_id: 374d700e-5dbb-4e00-929e-d570db5b1f8c
agent:    handed_off
host:     exit=137 verdict=killed_out_of_memory (622ms)
          Killed for using too much memory (out-of-memory).

$ python3 scripts/trace.py 374d700e-5dbb-4e00-929e-d570db5b1f8c
────────────────────────────────────────────────────────────────────────
trace 374d700e-5dbb-4e00-929e-d570db5b1f8c
────────────────────────────────────────────────────────────────────────

LangSmith  (inside the process)
  verdict : finished
  status  : success
  error   : none

Host observer  (outside the container)
  verdict : killed_out_of_memory
  exit    : 137
  means   : Killed for using too much memory (out-of-memory).
  took    : 548ms

────────────────────────────────────────────────────────────────────────
THE WATCHERS DISAGREE
  the inside watcher says the run finished; the host says exit 137 —
  killed for using too much memory (out-of-memory).
────────────────────────────────────────────────────────────────────────
```

`GET /trace/{trace_id}` is the same thing as a page, with the exact script and
the exact prompt that produced it.

**The disagreement is the demo.** One watcher says "fine", the other says
"dead, and here's the body" — under a single ID.

And LangSmith is not lying. It is not even wrong about what it saw: the agent
planned, wrote the code, handed it off, and returned, and every one of those
steps genuinely worked. The kill happened afterwards, in another process,
inside a container, somewhere LangSmith was never present. That is the whole
argument for putting the authoritative watcher one level up.

## Status

**Phase 4 — reconciliation (`v0.5-trace-view`).**

```bash
cp .env.example .env         # fill in keys; both are optional
make up                      # redis + api
make worker                  # the host observer, ON THE HOST, in a second shell
make run                     # a healthy run
make crash                   # a run that dies with 137
make test                    # unit tests + the real 137
python3 scripts/trace.py <trace-id>
```

`make worker` runs outside the compose stack on purpose. The observer cannot
live inside the thing it watches.

`GET /health` reports whether the LLM and LangSmith are live. Neither is
required: with no `OPENAI_API_KEY` the agent runs on a deterministic offline
model — a real LangChain chat model going through the same graph, prompts and
callbacks — so every phase, including the crash demo, works with no credentials.

The scenario flags (`healthy`, `oom`, `segfault`) are demo scaffolding and are
labelled as such in the source. A real pipeline gets bad code by accident;
waiting for that to happen is no way to prove a failure path works.

Built on `dev`, one milestone tag per phase.
