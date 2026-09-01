import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

export const GET: APIRoute = async ({ site }) => {
  const cases = await getCollection('cases', ({ data }) => !data.draft);
  const paths = [
    '/',
    '/work',
    '/about',
    '/contact',
    ...cases.map((c) => `/work/${c.slug}`),
  ];

  // Trailing slash on every path but the root. The build emits directories, so
  // the host answers `/work` with a 308 to `/work/` — listing the unslashed
  // form pointed every crawler at a redirect rather than at the page.
  const urls = paths
    .map((path) => (path === '/' ? path : `${path}/`))
    .map((path) => `  <url><loc>${new URL(path, site).href}</loc></url>`)
    .join('\n');

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
