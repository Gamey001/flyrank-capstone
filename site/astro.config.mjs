// @ts-check
import { defineConfig } from 'astro/config';

const site = process.env.SITE_URL ?? 'https://flyrank-capstone.pages.dev';

export default defineConfig({
  site,
  build: { inlineStylesheets: 'auto' },
});
