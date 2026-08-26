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

Optional: `PUBLIC_CONTACT_ENDPOINT`, a form POST endpoint. Set it and the
contact page renders a three-field form that posts there with no JavaScript.
Leave it unset and the page renders the direct-email path instead — deliberately,
because a form that posts nowhere and says "thanks" is the exact failure the lead
case study is about.

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
