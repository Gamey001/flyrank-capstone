import { readdir, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';

const DIST = process.argv[2] ?? 'dist';

const AMBER = /(#c8841f|#e0a13c|rgb\(\s*200[,\s]+132[,\s]+31)/i;

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

  for (const match of source.matchAll(COLOR_DECL)) {
    const value = match[2].trim();
    if (AMBER.test(value) || /var\(\s*--amber/i.test(value)) {
      violations.push({ path, decl: `color: ${value}` });
    }
  }

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
