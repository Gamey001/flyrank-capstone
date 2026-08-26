import { defineCollection, z } from 'astro:content';

const cases = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      title: z.string().min(3),

      order: z.number().int().positive(),

      oneLiner: z.string().min(10).max(140),

      headlineMetric: z.string().optional(),

      problem: z.string().min(40),

      approach: z.string().min(40),

      architectureImage: z.string().optional(),
      architectureAlt: z.string().optional(),
      architectureCaption: z.string().optional(),

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

      shipped: z.array(z.string().min(5)).min(1),

      result: z
        .array(
          z.object({
            label: z.string(),
            value: z.string(),
            note: z.string().optional(),
          }),
        )
        .min(1),

      figures: z
        .array(
          z.object({
            src: image(),
            alt: z.string(),
            caption: z.string().optional(),
          }),
        )
        .default([]),

      repo: z.string().url().optional(),
      demo: z.string().url().optional(),
      demoLabel: z.string().optional(),

      tags: z.array(z.string()).default([]),

      traceId: z.string().optional(),

      draft: z.boolean().default(false),
    }),
});

export const collections = { cases };
