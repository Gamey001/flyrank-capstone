/**
 * The handful of facts that appear on more than one page. One place to
 * change them, so the footer and the contact page can never drift apart.
 */

export const site = {
  name: 'Gamaliel Dashua',
  role: 'Backend / AI Engineer',

  /** The one sentence a visitor should remember. */
  claim:
    'I build observable AI agent pipelines you can trace end-to-end — every step back to one ID.',

  subline:
    'When a run fails, one ID links the failure to the exact step, prompt and model call that caused it — including the failures that normally leave no trace at all.',

  /** The single desired action. Repeated in every footer, never expanded. */
  action: {
    label: 'Book a 20-min call',
    note: 'or send a take-home — I would rather be assessed on work than on a CV.',
  },

  email: 'gamalieldashua@gmail.com',
  github: 'https://github.com/Gamey001',
  githubLabel: 'github.com/Gamey001',
  linkedin: 'https://www.linkedin.com/in/gamaliel-dashua',
  linkedinLabel: 'linkedin.com/in/gamaliel-dashua',

  capstoneRepo: 'https://github.com/Gamey001/flyrank-portfolio-site',

  /** Production credibility, in one line. */
  proof:
    'Shipped and maintained LAMISPlus, the national HIV/AIDS electronic medical record deployed across Nigerian treatment facilities.',

  stack: ['Java / Spring', 'FastAPI', 'LangGraph', 'React / TypeScript'],
} as const;

/**
 * The numbers, kept together so every page quotes the same ones and each
 * has a source you can name out loud in an interview.
 */
export const numbers = {
  /** Entry · plan · write code · hand-off · run · format. */
  pipelineSteps: 6,
  /** All six carry the ID, including the one written after the process dies. */
  stepsTraced: 6,
  beforeDebug: '~14 hrs',
  afterDebug: 'under 2 min',
} as const;

/**
 * One or two lines from someone who managed the work, with a name and a role
 * attached. Left undefined until there is a real one to quote — an unattributed
 * testimonial is worth less than no testimonial, and the About page renders
 * nothing at all while this is undefined.
 */
export const testimonial: { quote: string; name: string; role: string } | undefined =
  undefined;

export const nav = [
  { href: '/', label: 'Home' },
  { href: '/work', label: 'Work' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
] as const;
