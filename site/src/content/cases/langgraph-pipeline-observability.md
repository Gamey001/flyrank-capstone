---
title: LangGraph agent pipeline observability
order: 1
oneLiner: One trace ID that survives the crash LangSmith cannot see, because the authoritative watcher sits outside the process that dies.
headlineMetric: root cause — ~14 hrs → under 2 min
traceId: 4161ab9f-17f7-4ced-a552-2ba12de4e6cc

problem: >-
  An AI-written code step crashed, caught its own exception, reported success and
  exited cleanly. An enterprise customer's morning reports came back blank while
  every dashboard stayed green. Finding out why meant combing through logs by hand
  across several services, guessing which of thousands of runs was the bad one. It
  took roughly fourteen hours. Nothing about that is exotic — it is what happens
  whenever the thing that reports a failure is running inside the thing that failed.

approach: >-
  The thing that watches for failure cannot be the thing that might die. A smoke
  alarm wired to the same power as the stove will not ring when the stove catches
  fire and cuts the power. So the authoritative watcher was moved one level up: it
  lives on the host, outside the container, where it can still speak after the
  container is gone. LangSmith is kept, not rebuilt — it gives the rich view of every
  model call, and none of that is reimplemented. It simply is not the last word.

architectureImage: /diagrams/architecture.svg
architectureAlt: >-
  Six pipeline steps in a row — entry, plan, write code, hand-off, run, format. A
  navy rail runs beneath them with an amber marker at each step, labelled with the
  trace ID. LangSmith's band covers only the agent process and stops at the queue
  boundary. The host observer sits outside the container and writes the final record
  under the same ID after the container has exited.
architectureCaption: >-
  The trace ID is minted once at entry, stamped onto every model call, carried across
  the queue inside a three-field envelope, and passed into the container as an
  environment variable. The last record under that ID is written on the host, after
  the container has fully exited — which is exactly why a 137 cannot erase it.

snippets:
  - caption: app/agent/graph.py — the ID goes onto every model call
    lang: python
    highlight: [5, 7]
    code: |
      def stamped(config: RunnableConfig, trace_id: str, name: str) -> RunnableConfig:
          """Attach the trace ID to a model call."""
          cfg = dict(config or {})
          metadata = dict(cfg.get("metadata") or {})
          metadata["trace_id"] = trace_id
          tags = list(cfg.get("tags") or [])
          tags.append(f"trace:{trace_id}")
          cfg["metadata"] = metadata
          cfg["tags"] = tags
          cfg["run_name"] = name
          return cfg
  - caption: app/envelope.py — three fields cross the queue, and only three
    lang: python
    highlight: [1, 5]
    code: |
      FIELDS = ("trace_id", "generated_code", "source_prompt")

      @dataclass(frozen=True)
      class ExecutionEnvelope:
          trace_id: str
          generated_code: str
          source_prompt: str

          @classmethod
          def from_json(cls, raw: str) -> "ExecutionEnvelope":
              data = json.loads(raw)
              missing = [f for f in FIELDS if f not in data]
              if missing:
                  raise ValueError(f"envelope missing fields: {', '.join(missing)}")
              return cls(**data)
  - caption: app/worker/host_observer.py — the last record, written from outside
    lang: python
    highlight: [4]
    code: |
      # By the time this runs the container is gone. The exit code was read
      # from outside it, and so is the record that survives it.
      return Outcome(
          trace_id=envelope.trace_id,
          exit_code=exit_code,
          verdict=verdict,
          explanation=explanation,
          duration_ms=int((time.monotonic() - started) * 1000),
          source_prompt=envelope.source_prompt,
          generated_code=envelope.generated_code,
      )

shipped:
  - A LangGraph agent that plans a customer report, writes a Python script to produce it, and hands the script off across a Redis queue — content as the deliverable, code execution as the thing that can fail hard.
  - A host observer that runs outside the compose stack, starts the sandbox container, and reads the exit code from the outside. It is deliberately absent from docker-compose.yml; a watcher inside the stack dies with it.
  - A paste-one-ID view, as both a CLI and an HTML page, showing what each watcher saw side by side and naming which one is authoritative.
  - A quality gate that reads what the run produced rather than how the process exited, so a script that exits 0 with an empty report is caught instead of shipped.
  - Quarantine — a dead or empty run is held back before anything can read it, still reachable by its ID, with the reason beside the record that caused it.
  - Replay — POST /runs/{id}/replay re-runs a failure from its ID alone; the prompt and script come back out of the outcome record, and the replay gets its own ID pointing at the original rather than overwriting the evidence.
  - A test that kills a real container with a real 137 and asserts the record still exists afterwards. That test is what defines the boundary.

result:
  - label: Time to root cause
    value: ~14 hrs → under 2 min
    note: Before, log-diving across services. After, one ID returns both watchers, the exit code, the exact script and the prompt that produced it.
  - label: Steps carrying the ID
    value: 6 of 6
    note: Entry, plan, write code, hand-off, run, format — including the record written after the process is gone.
  - label: Failures an inside watcher misses
    value: 3 of 3 caught
    note: Hard kill (137), hard crash (139) and the swallowed error that exits 0. All three are caught from outside.
  - label: Runtime dependencies to reproduce
    value: 0 API keys
    note: With no OPENAI_API_KEY the agent runs a deterministic offline model through the same graph, prompts and callbacks, so the crash demo works with no credentials.

figures:
  - src: ../../assets/cases/trace-view.png
    alt: >-
      The trace page for one run. A navy trace ID with an amber marker beside it, a
      banner reading "The watchers disagree", a quarantine notice, and two cards —
      LangSmith reporting "finished" and the host observer reporting
      "killed_out_of_memory" with exit code 137 and the exact script that ran.
    caption: >-
      GET /trace/{id}. The disagreement is the demo: one watcher says fine, the other
      says dead and here is the body — under a single ID. LangSmith is not lying. The
      agent planned, wrote the code and handed it off, and all of that genuinely worked.
      The kill happened afterwards, somewhere it was never present.
  - src: ../../assets/cases/before-after.png
    alt: >-
      Two terminal panels. On the left, "Before — the black-box run": LangSmith reports
      status success with no error, the report is null, and grepping the service logs
      for errors or for exit 137 returns zero hits while every service reads as up. On
      the right, "After — paste one ID": scripts/trace.py prints both watchers under one
      trace ID, the host reporting exit 137, killed for using too much memory, and the
      run held in quarantine.
    caption: >-
      The same failing run, twice. Left is everything an inside-the-process watcher can
      tell you: green, no error line, and an empty report. The process that died was
      never in those logs. Right is the same run by its ID.
  - src: ../../assets/cases/quality-gate.png
    alt: >-
      The trace page for a run that exited 0. Both watchers report the run finished, but
      the host observer's quality gate reads "exited 0 but did not produce the report it
      planned" and the run is held in quarantine.
    caption: >-
      The third failure, and the one from the original incident. Exit code 0 means the
      script finished, not that it produced a report. Only something reading the output
      can tell, so the gate runs on the host after the container is gone.

repo: https://github.com/Gamey001/flyrank-capstone
tags: [LangGraph, LangChain, LangSmith, FastAPI, Redis, Docker]
---

LangSmith is genuinely useful and it is kept. But it watches from inside the running
process, and a record that opens when a step starts only closes when the step returns.
Three failures break that, and all three are ordinary:

| Failure | What an inside-the-process watcher sees |
| --- | --- |
| Hard kill — `137` out-of-memory, `139` crash | Nothing, or a record stuck half-open. The closing line never runs. |
| Swallowed error | A green, successful record. It lies. |
| Death across a process boundary | The watcher was never present in the helper that died. |

The hand-off is where the argument lives. The agent does not wait for the generated code
to run, because the code runs in another process behind a queue boundary. Pretending
otherwise would be the same lie the original incident was made of — so the pipeline is
built to admit it, and the watcher is placed where the admission still costs nothing.

Once one ID reaches everything, replay, quarantine and the quality gate stop being
separate products and become branches of the same trace. That is the payoff of spending
the effort on the spine rather than on a dashboard.

Three extensions are left deliberately unbuilt, because they only prove out against a
live production graph: drift monitoring at real traffic volumes, automatic root-cause
grouping across thousands of failing traces, and carrying the same ID through services
beyond this pipeline. Those seams are open on purpose.
