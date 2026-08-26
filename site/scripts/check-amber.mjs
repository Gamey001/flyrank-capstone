/**
 * The amber rule, enforced against the built output.
 *
 * Amber is never the text and never a link. <TraceMarker> makes that easy to
 * follow by hand; this makes it impossible to break by accident, because it
 * reads the CSS that actually shipped rather than the source that was meant
 * to ship.
 *
 * A `color:` declaration resolving to the amber token is a failure. Amber as
 * `background`, `border-*`, `outline`, `fill` or `stroke` is the rule working
 * as intended — the mark goes beside the thing.
 *
 *   node scripts/check-amber.mjs [distDir]
 */
import { readdir, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';

const DIST = process.argv[2] ?? 'dist';

// Every way the palette's amber can be written.
const AMBER = /(#c8841f|#e0a13c|rgb\(\s*200[,\s]+132[,\s]+31)/i;

// A `color:` that is not part of a longer property name (border-color,
// outline-color, -webkit-text-fill-color, …).
const COLOR_DECL = /(^|[;{}\s])color\s*:\s*([^;}]+)/gi;

async function* files(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* files(path);
    else if (['.css', '.html'].includes(extname(entry.name))) yield path;
  }
}

const violations = [];

for await (const path of files(DIST)) {
  const source = await readFile(path, 'utf8');

  // Resolve `color: var(--amber)` too: if a custom property named *amber*
  // is used as a colour value, that is the same violation.
  for (const match of source.matchAll(COLOR_DECL)) {
    const value = match[2].trim();
    if (AMBER.test(value) || /var\(\s*--amber/i.test(value)) {
      violations.push({ path, decl: `color: ${value}` });
    }
  }

  // Inline `style="color: …"` in markup, and any stray amber anchor rule.
  for (const match of source.matchAll(/<a\b[^>]*style="([^"]*)"/gi)) {
    if (AMBER.test(match[1]) && /(^|;)\s*color\s*:/i.test(match[1])) {
      violations.push({ path, decl: `inline link colour: ${match[1]}` });
    }
  }
}

if (violations.length > 0) {
  console.error('\nThe amber rule is broken. Amber is never text and never a link.\n');
  for (const v of violations) console.error(`  ${v.path}\n    ${v.decl}`);
  console.error(
    '\nTo mark something, put amber beside it — a dot, a stripe, an underline —\n' +
      'or use dark text on an amber ground. <TraceMarker> does all three.\n',
  );
  process.exit(1);
}

console.log(`amber rule: clean (${DIST})`);
