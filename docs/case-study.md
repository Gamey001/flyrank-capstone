# One trace ID that survives the crash

## The incident this is based on

An AI-written code step crashed. It caught its own exception, reported success,
and exited cleanly. An enterprise customer's morning reports came back blank
while every dashboard stayed green. Finding out why meant combing through logs
by hand across several services, guessing which of thousands of runs was the
bad one. It took roughly fourteen hours.

Nothing about that is exotic. It is what happens when the thing that reports a
failure is running inside the thing that failed.

## The principle

> **The thing that watches for failure cannot be the thing that might die.**

A smoke alarm wired to the same power as the stove will not ring when the stove
catches fire and cuts the power. You needed the one thing that could not
survive the event to warn you about the event.

So the authoritative watcher has to sit outside the thing it is watching. In
this build it lives on the host, one level above the container, where it can
still speak after the container is gone.

## Why LangSmith is kept and not rebuilt

LangSmith gives the rich view of every model call — prompt, tokens, timings —
and none of that is reimplemented here. But it watches from inside the running
process, and a run record that opens when a step starts only closes when the
step returns. Three failures break that:

| Failure | What an inside-the-process watcher sees |
| --- | --- |
| Hard kill (`137`, `139`) | Nothing, or a record stuck half-open. The closing line never runs. |
| Swallowed error | A green, successful record. It lies. |
| Death across a process boundary | It isn't present in the helper that died. |

This is not a criticism of LangSmith. It is the reason the principle exists: an
inside-the-process watcher is, by definition, inside the danger zone.

## What the system does

An agent builds a customer report by writing a small script and then running
it. Content as the deliverable, code execution as the thing that can fail hard.

1. **Entry** — a request arrives and the trace ID is minted. Once, in one place.
2. **Plan** — the agent decides what the report needs.
3. **Write code** — the agent writes a script to produce it.
4. **Hand-off** — the script, the prompt that produced it, and the trace ID go
   onto a Redis queue in a three-field envelope. The agent then returns.
5. **Run** — the host observer picks the envelope up, starts a container, feeds
   the script in, and reads the exit code from outside.
6. **Format** — at read time, if the run is shippable, its output becomes the
   report.

Step 4 is where the argument lives. The agent does not wait for the code to
run, because the code runs in another process behind a queue boundary.
Pretending otherwise would be the same lie the incident was made of.

## The trace ID's journey

| Where | What happens to the ID |
| --- | --- |
| Entry | Minted once, a UUIDv4. The only place it is created. |
| Through the agent | Carried in pipeline state and stamped onto every model call, so LangSmith's records line up under it. |
| Across the queue | Travels inside the envelope: `trace_id`, `generated_code`, `source_prompt`. Three fields, validated on the way out. |
| Into the container | Passed in as an environment variable. The box knows its ID; the host does not depend on it to report it back. |
| At the failure | The host writes the outcome under that same ID, from outside the box. |

**The test that defines the boundary:** the last trace record is written *on the
host, after the container has fully exited*, from the exit code the host
collected. Inside the container, a `137` would wipe it out before it could be
saved.

## Before and after

**Before.** A run fails, the dashboard is green, and you go log-diving across
services for hours with nothing to follow.

**After.** You paste one trace ID and get both views side by side:

- **LangSmith says:** the run finished. Green. `status: success`, no error.
- **The host observer says:** exit code `137` — killed for memory — and here is
  the exact prompt and the exact script that killed it.

**The disagreement is the demo.** One watcher says "fine", the other says
"dead, and here's the body", under a single ID.

And LangSmith is not wrong about what it saw. The agent planned, wrote the code
and handed it off, and every one of those steps genuinely worked. The kill
happened afterwards, in another process, inside a container — somewhere
LangSmith was never present. That is the entire argument for putting the
authoritative watcher one level up.

## The third failure: exit code 0

A clean exit is necessary and not sufficient. The `swallowed` scenario exits 0
with an empty report, exactly like the original incident, and every watcher
looking at the *process* sees success. Only something reading what the run
actually *produced* can tell — so the quality gate runs on the host, after the
container is gone, and holds the run in quarantine. Nothing ships.

## What falls out of the spine

Once one ID reaches everything, these are branches of the same trace rather
than separate products:

- **Replay** — the prompt and the script come back out of the outcome record,
  so a failing run re-runs from its ID alone. The replay gets its own ID
  pointing at the original; overwriting it would destroy the evidence.
- **Quarantine** — a run that died, or exited clean and produced nothing, is
  held back before anything can read it.
- **The quality gate** — shown in miniature.

## Left deliberately unbuilt

These are real extensions of the same spine that only prove out against a live
production graph — which is exactly what a take-home would give you:

- **Live drift monitoring at scale.** The quality gate is shown in miniature;
  proving it needs real traffic over time.
- **Automatic root-cause grouping.** Clustering thousands of failing traces by
  shared cause.
- **Cross-service propagation.** Carrying the same ID through services beyond
  this one pipeline.

These seams are left open on purpose.

## Stack

LangGraph · LangChain · LangSmith · FastAPI · Redis · Docker. Runs locally.
The demo is the disagreement, not the hosting.
