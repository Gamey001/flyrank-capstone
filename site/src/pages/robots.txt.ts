import type { APIRoute } from 'astro';

// Generated rather than served from /public because the Sitemap directive has
// to be an absolute URL — the robots.txt spec gives it no base to resolve
// against, so crawlers discard a relative path and never find the sitemap.
// Only `site` knows the origin, and it changes with SITE_URL.
export const GET: APIRoute = ({ site }) =>
  new Response(
    ['User-agent: *', 'Allow: /', '', `Sitemap: ${new URL('/sitemap.xml', site).href}`, ''].join('\n'),
    { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
  );
