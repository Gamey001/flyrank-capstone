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
{scenario_note}
Write the script that produces this report."""


SCENARIO_NOTES = {
    "healthy": "",
    "oom": (
        "\nThe script must also allocate memory in a loop without bound, so "
        "that it exceeds a 128MB container limit and is killed.\n"
    ),
    "segfault": (
        "\nThe script must also dereference a null pointer via ctypes so that "
        "the interpreter segfaults.\n"
    ),
    "swallowed": (
        "\nThe script must wrap its work in a broad try/except that swallows "
        "any error, and print whatever it has when that happens, so that it "
        "always exits 0.\n"
    ),
}


def scenario_note(scenario: str) -> str:
    if scenario not in SCENARIO_NOTES:
        raise ValueError(
            f"unknown scenario {scenario!r}; "
            f"expected one of {', '.join(SCENARIO_NOTES)}"
        )
    return SCENARIO_NOTES[scenario]
