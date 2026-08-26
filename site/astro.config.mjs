// @ts-check
import { defineConfig } from 'astro/config';

const site = process.env.SITE_URL ?? 'https://flyrank-portfolio-site.pages.dev';

export default defineConfig({
  site,
  build: { inlineStylesheets: 'auto' },
});
