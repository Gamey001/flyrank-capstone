# Portfolio site

The site that frames the observability capstone. Four pages, no JavaScript
shipped, no CMS, no database, no server.

The capstone itself lives in the repository root — this directory is only the
site that shows it.

## Run it

```bash
npm install
npm run dev        # http://localhost:4321
npm run verify     # astro check + build + the amber-rule guard
```

Node 18.20+ or 20.3+ (built and tested on 22.6).

## Deploy — Cloudflare Pages

Connect the GitHub repository and set:

| Setting | Value |
| --- | --- |
| Framework preset | Astro |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory | `site` |
| Node version | `NODE_VERSION=22` |

Then set `SITE_URL` to the live origin (for example
`https://gamalieldashua.dev`) so canonical links, the sitemap and the Open Graph
card point at the real domain rather than the `.pages.dev` fallback.

## The contact form

The one dynamic thing here. Everything else is a file served as-is; `/api/contact`
is code that runs when someone submits.

`functions/api/contact.ts` is a Cloudflare Pages Function. Pages picks up
`functions/` automatically from the root directory (`site`) — Astro does not
build it, and it is not part of `dist`. It validates the three fields, drops
honeypot submissions, calls the Resend API, and answers with a 303 to
`/contact/sent` or `/contact/problem`. No JavaScript is involved on either side.

One secret, set as an environment variable on the Pages project (never in the repo):

| Variable | Required | What it is |
| --- | --- | --- |
| `RESEND_API_KEY` | yes | Resend API key. Set the type to **Secret** — it can send mail as you. |
| `CONTACT_FROM` | no | Defaults to `onboarding@resend.dev`. Set to an address on your own domain once that domain is verified in Resend. |

The recipient is **not** configuration. It is `site.email`, imported from
`src/site.ts` — the same value the contact page prints — so the inbox that
receives a submission cannot drift from the address the site tells people to
write to. It is not a secret; it is on the page. Making it a variable only added
a way to break the form from a dashboard.

Note that Resend's free tier will only deliver to the address the Resend account
was registered under until you verify a domain. So on the free tier `site.email`
and the Resend account email have to be the same address.

With `RESEND_API_KEY` missing the function refuses the send, logs
`contact: not configured, missing RESEND_API_KEY`, and redirects to
`/contact/problem` — deliberately, because a form that posts nowhere and says
"thanks" is the exact failure the lead case study is about.

Pages injects variables at build time, so setting one does not affect the
deployment already live. Retry the deployment after adding it.

### Rate limiting

The function throttles to 5 sends per address per 10 minutes, but **measurement
says treat that as worth nothing**. Sixteen rapid submissions from one address
against the deployed function were all accepted: the counter lives in one
isolate's memory, and requests land in a fresh or different isolate often enough
that it is almost always empty. It is kept because it costs nothing and does
stop a burst that happens to land together, not because it is protection.

**The only control that actually holds has to be set in the dashboard**, and is
not in this repo:
Security → WAF → Rate limiting rules, matching `http.request.uri.path eq
"/api/contact"` and `http.request.method eq "POST"`, something like 5 requests
per minute per IP, action Block. Free tier includes one rule. Without it the
endpoint can be used to drain the Resend allowance.

Run it locally the way Cloudflare runs it — `astro dev` alone serves the pages
but not the function:

```bash
npm run build
npx wrangler pages dev dist          # http://localhost:8788
```

Add `--binding RESEND_API_KEY=...` to test a real send. Note that the Workers
runtime needs macOS 13.5+; on older macOS `wrangler pages functions build`
still compiles the function, but only a deployment can run it.

Optional: `PUBLIC_CONTACT_ENDPOINT` overrides the form's `action`, to point at a
third-party form service instead of this function.

## The shape of it

```
src/
  site.ts                 the handful of facts used on more than one page
  styles/tokens.css       every colour and spacing value, named once
  styles/base.css         typography, links, focus, skip link
  components/             Nav, Footer, ContactBand, Hero, CaseCard,
                          TraceMarker, CodeSnippet, ProofStrip, SectionRule
  layouts/                BaseLayout, CaseStudyLayout (the seven beats)
  content/cases/*.md      one file per case study
  pages/                  index, work, work/[...slug], about, contact, 404
scripts/check-amber.mjs   the amber rule, checked against the built CSS
```

## Two rules worth knowing before editing

**The amber rule.** Amber (`#C8841F`) is never the text and never a link. To
mark a trace ID, the ID stays navy and amber goes beside it — a dot, a left
stripe — or dark text sits on an amber ground. `<TraceMarker>` implements all
three, and `npm run check:amber` fails the build if a `color:` declaration ever
resolves to amber. There is no `--amber-text` token and there should not be one.

**Adding a case study is dropping in a file.** `src/content/cases/` holds one
markdown file per case with a fixed frontmatter shape, validated at build time.
Adding "Case 06" means adding a file — no layout is touched and no page is
edited. A half-filled case fails the build rather than shipping blank, which is
the same argument the capstone makes about exit code 0: finishing is not the
same as producing the thing you promised.
