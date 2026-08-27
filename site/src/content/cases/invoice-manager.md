---
title: Invoice manager and dashboard
order: 5
oneLiner: A full-stack invoicing tool — the ordinary CRUD-and-reporting work, done cleanly.
headlineMetric: full-stack range

problem: >-
  Invoicing is the kind of application where the requirements look trivial and the edge
  cases are not: partial payments, credit notes, a total that has to agree with itself
  across three views, and a number no one is allowed to see change after it has been
  sent.

approach: >-
  Keep money out of floating point, derive every displayed total from one calculation
  rather than recomputing it per view, and make issued documents immutable. Most of the
  bugs in this class of application come from the same total being worked out in two
  places and drifting.

shipped:
  - A full-stack invoicing application — create, issue, track and report — with a dashboard over the current state.
  - One calculation path for totals, reused by every view that displays them.

result:
  - label: Scope
    value: Full stack
    note: Data model, API and interface, kept small enough to reason about end to end.
  - label: Why it is here
    value: Range, briefly
    note: Included to show breadth. The capstone and LAMISPlus carry the argument.

repo: https://github.com/Gamey001/invoice-app
demo: https://inspiring-boba-3545a8.netlify.app/
tags: [Full-stack, Dashboard]
---
