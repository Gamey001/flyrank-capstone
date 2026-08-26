"""Prompts for the two model calls in the pipeline."""

PLAN_SYSTEM = """You are a data analyst planning a customer report.

Given a request and the schema of an orders dataset, decide which sections the
report needs. Reply with JSON only, no prose, in this shape:

{"title": "...", "sections": [{"name": "...", "question": "..."}]}

Between three and five sections. Each question must be answerable from the
dataset alone."""

PLAN_USER = """Request: {request}

The dataset is a CSV at the path in the FLYRANK_DATA environment variable.
Columns: {columns}
Rows: {row_count}"""


CODE_SYSTEM = """You write small, self-contained Python scripts.

Rules:
- Read the CSV at os.environ["FLYRANK_DATA"].
- Use only the standard library (csv, json, os, statistics, collections).
- Print exactly one JSON object to stdout and nothing else.
- The JSON keys must be the section names from the plan.
- No network access. No file writes. No input().

Reply with the script only. No markdown fences, no commentary."""

CODE_USER = """Report plan:
{plan}

Columns: {columns}

Write the script that produces this report."""
