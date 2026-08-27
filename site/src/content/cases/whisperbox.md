---
title: WhisperBox
order: 4
oneLiner: An encrypted chat application, built to think properly about what the server is allowed to know.
headlineMetric: security-minded engineering

problem: >-
  Most chat applications are secure in the sense that traffic is encrypted in transit and
  the operator can still read everything. That is a different property from the one users
  assume they have. Building the stronger version forces you to decide, explicitly, what
  the server is permitted to learn.

approach: >-
  Start from the threat model rather than the feature list, and let it decide the data
  model. If the server should not be able to read message contents, then the design has
  to make that structurally true rather than a matter of policy — which changes where
  keys live, what the server stores, and which features are possible at all.

shipped:
  - An end-to-end encrypted chat application with the key handling and message flow built around what the server is deliberately not given.
  - Feature decisions documented against the threat model, including the ones that were dropped because they would have required the server to read too much.

result:
  - label: Design driver
    value: Threat model first
    note: The data model follows from what the server is allowed to know, not the other way round.
  - label: Trade-off made explicit
    value: Features vs. server knowledge
    note: Capabilities that would have required plaintext on the server were cut rather than weakened.

repo: https://github.com/Gamey001/chatty-messge-app
demo: https://incomparable-churros-927646.netlify.app/
tags: [Security, Encryption, Full-stack]
---
