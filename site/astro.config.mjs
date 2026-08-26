// @ts-check
import { defineConfig } from 'astro/config';

// The deployed origin. Set SITE_URL in Cloudflare Pages once the custom
// domain is attached; canonical links and the Open Graph card read from it.
const site = process.env.SITE_URL ?? 'https://flyrank-portfolio-site.pages.dev';

export default defineConfig({
  site,
  // No app framework, no client-side router, no islands. Astro ships zero
  // JavaScript here on purpose — see the anti-over-engineering list in the spec.
  build: { inlineStylesheets: 'auto' },
});
