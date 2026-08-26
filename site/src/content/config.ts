import { defineCollection, z } from 'astro:content';

/**
 * A case study is one file with a fixed shape. Adding "Case 06" is dropping
 * in a file — no layout is touched, no page is edited.
 *
 * TypeScript validates the shape at build time, so a half-filled case fails
 * the build loudly instead of shipping blank. That is the same argument the
 * capstone makes about exit code 0: finishing is not the same as producing
 * the thing you promised.
 */

const cases = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      /** Case title, as it appears everywhere. */
      title: z.string().min(3),

      /** Sort order across /work and the home cards. Lead case is 1. */
      order: z.number().int().positive(),

      /** One line. Shown on every card. Keep it under ~110 characters. */
      oneLiner: z.string().min(10).max(140),

      /** The number a reader should leave with. Rendered on an amber pill. */
      headlineMetric: z.string().optional(),

      /** Beat 1. What was wrong, in the reader's terms. */
      problem: z.string().min(40),

      /** Beat 2. The decision that resolved it, and why that one. */
      approach: z.string().min(40),

      /** Beat 3. The diagram, served from /public so the SVG ships as-is. */
      architectureImage: z.string().optional(),
      architectureAlt: z.string().optional(),
      architectureCaption: z.string().optional(),

      /**
       * Shown under the diagram. Each is a real excerpt from the repository,
       * with the line carrying the trace ID marked — <CodeSnippet> puts amber
       * beside that line rather than in it.
       */
      snippets: z
        .array(
          z.object({
            caption: z.string(),
            lang: z.string().optional(),
            code: z.string(),
            highlight: z.array(z.number().int().positive()).default([]),
          }),
        )
        .default([]),

      /** Beat 4. What actually got built. */
      shipped: z.array(z.string().min(5)).min(1),

      /** Beat 5. Numbers, each with a note saying where it comes from. */
      result: z
        .array(
          z.object({
            label: z.string(),
            value: z.string(),
            note: z.string().optional(),
          }),
        )
        .min(1),

      /**
       * Supporting captures. Optional on purpose: a case with no screenshot
       * renders without a figure rather than shipping a placeholder box.
       */
      figures: z
        .array(
          z.object({
            src: image(),
            alt: z.string(),
            caption: z.string().optional(),
          }),
        )
        .default([]),

      /** Beat 6. */
      repo: z.string().url().optional(),
      demo: z.string().url().optional(),
      demoLabel: z.string().optional(),

      tags: z.array(z.string()).default([]),

      /** A trace ID to display through <TraceMarker>. Lead case only. */
      traceId: z.string().optional(),

      /** Kept off /work and the home cards while a case is being written. */
      draft: z.boolean().default(false),
    }),
});

export const collections = { cases };
