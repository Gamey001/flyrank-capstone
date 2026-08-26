# Assets — what is real, and what is still missing

The proof on this site rests on the images. This file says exactly which ones
are real captures, and exactly where to drop the ones that still need you.

## Already real — captured from the running capstone

These were produced by starting the pipeline (`make up`, `make worker`) and
running the actual scenarios, then screenshotting what came back. The trace IDs
in them are real IDs from those runs.

| File | What it is |
| --- | --- |
| `src/assets/cases/trace-view.png` | `GET /trace/{id}` for a run killed with exit 137. The disagreement banner, the quarantine notice, both watcher cards, and the exact script that ran. |
| `src/assets/cases/quality-gate.png` | `GET /trace/{id}` for the `swallowed` run — exit 0, empty report, held by the quality gate. |
| `src/assets/cases/before-after.png` | The black-box run beside the paste-one-ID run. Every command in the left panel was run against the live stack and its output is unedited. |
| `public/diagrams/architecture.svg` | The six pipeline steps with the trace ID running beneath them, LangSmith's reach stopping at the queue boundary, and the host observer outside the container. Authored, not captured. |
| `public/og.png` | The Open Graph card. |
| `public/favicon.svg` | The pipeline glyph — three nodes, terminal node amber. Checked for legibility at 16px. |

To regenerate the two trace captures after changing the capstone: start the
stack, run a scenario, and screenshot `http://localhost:8000/trace/<id>` at
1280px wide.

## Still needed from you

Nothing here ships a placeholder. Where an asset is missing the layout simply
omits the figure, so the site is honest today and gets better the moment you
add a file.

### 1. Your photograph — About page

Drop a real professional photo at **`src/assets/portrait.jpg`** (or `.png` /
`.webp`). The About page detects it and switches to the two-column layout on its
own; no code change. Portrait-ish crop, at least 640px on the short edge. No
generated portrait — the spec is explicit and a reader can tell.

### 2. LAMISPlus UI — `src/content/cases/lamisplus-national-emr.md`

**Hard gate: confirm what is public before capturing anything.** Dummy records
only, no patient data, no facility identifiers, no PII of any kind. When you
have a clean capture, put the file in `src/assets/cases/` and add:

```yaml
figures:
  - src: ../../assets/cases/lamisplus.png
    alt: <describe what is on screen, for a reader who cannot see it>
    caption: <one line, and say the data is dummy>
```

### 3. Logbookie and WhisperBox — one clean screenshot each

Same shape, in `src/content/cases/logbookie.md` and
`src/content/cases/whisperbox.md`.

### 4. Numbers to replace with your real figures

The lead case's numbers all come from the capstone and are real. These are the
ones written qualitatively because I could not verify a figure:

- **`lamisplus-national-emr.md` → `result`** — facility count, patient records
  under management, years in production. Replace the `Scope` entry's `value`
  and `note` with the real figures once you have a public source for them.
- **`logbookie.md` → `result`** — contract length, or what you shipped, if you
  are able to say.
- **`whisperbox.md` / `invoice-manager.md`** — anything measurable.

Do not add a number you cannot source in an interview. The site currently makes
no claim it cannot back, and that is worth more than a rounder figure.

### 5. Deployed demo or Loom for the capstone

`langgraph-pipeline-observability.md` has `repo` set and no `demo`. When a
deployment or a short walkthrough exists:

```yaml
demo: https://…
demoLabel: Watch the 3-minute walkthrough
```

The Links beat renders it automatically.

### 6. A testimonial

`src/site.ts` exports `testimonial`, currently `undefined`. Fill it in and the
About page renders it; leave it and nothing appears. One or two lines, with a
real name and role attached:

```ts
export const testimonial = {
  quote: '…',
  name: '…',
  role: '…',
};
```

### 7. Contact endpoint (optional)

Set `PUBLIC_CONTACT_ENDPOINT` in Cloudflare Pages to a form POST endpoint and
the contact page swaps the direct-email path for a three-field form. Name, email
and one line — never more than that.

## Connective imagery

There is none, and there should be none. Whitespace does that job.
