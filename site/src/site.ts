export const site = {
  name: 'Gamaliel Dashua',
  role: 'Backend / AI Engineer',

  claim:
    'I build observable AI agent pipelines you can trace end-to-end — every step back to one ID.',

  subline:
    'When a run fails, one ID links the failure to the exact step, prompt and model call that caused it — including the failures that normally leave no trace at all.',

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

  proof:
    'Shipped and maintained LAMISPlus, the national HIV/AIDS electronic medical record deployed across Nigerian treatment facilities.',

  stack: ['Java / Spring', 'FastAPI', 'LangGraph', 'React / TypeScript'],
} as const;

export const numbers = {
  pipelineSteps: 6,
  stepsTraced: 6,
  beforeDebug: '~14 hrs',
  afterDebug: 'under 2 min',
} as const;

export const testimonial: { quote: string; name: string; role: string } | undefined =
  undefined;

export const nav = [
  { href: '/', label: 'Home' },
  { href: '/work', label: 'Work' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
] as const;
