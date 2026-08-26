---
title: LAMISPlus — national HIV/AIDS EMR
order: 2
oneLiner: Backend work on the electronic medical record Nigeria's national HIV/AIDS programme runs on.
headlineMetric: production at national scale

problem: >-
  A national treatment programme needs one record per patient that every facility can
  read, that keeps working where the network does not, and that never leaks a patient's
  identity. The failure modes are not aesthetic: a duplicated patient record splits a
  treatment history, and a sync that silently drops a visit means somebody's regimen is
  wrong at the next appointment.

approach: >-
  Treat correctness at the boundary as the whole job. Every write is validated against
  the programme's reporting definitions before it is accepted rather than cleaned up
  afterwards, because a record that reaches the database wrong has already been read by
  someone. The modular Spring service split keeps clinical modules independent, so a
  change to one programme area cannot quietly alter another's numbers.

shipped:
  - Backend modules in Java and Spring Boot against the shared patient record, built so each clinical area can change without touching the others.
  - Validation at the write boundary, matched to the national reporting definitions, so bad data is refused at the door rather than reconciled later.
  - Facility-level deployment and support work — installs, upgrades and the unglamorous debugging that keeps a record system usable in the places it is actually used.

result:
  - label: Scope
    value: National programme
    note: LAMISPlus is the electronic medical record used by Nigeria's national HIV/AIDS treatment programme, deployed across participating facilities.
  - label: Data handling
    value: No PII off-site
    note: Every screenshot and demo of this work uses dummy records only. Patient data does not leave the facility deployment, and none of it appears here.

tags: [Java, Spring Boot, PostgreSQL, Healthcare]
---

The reason this case sits second rather than first is that it proves a different thing
from the capstone. The capstone argues about design. This one is the evidence that the
design habits survive contact with production — a system real clinicians open every day,
where being wrong has a cost that is not measured in engineering time.
