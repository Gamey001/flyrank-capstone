"""The dataset the report is built from."""

from __future__ import annotations

import csv
import os
from pathlib import Path

from app.config import PROJECT_ROOT

DATA_PATH = Path(
    os.environ.get("FLYRANK_DATA", PROJECT_ROOT / "data" / "orders.csv")
)


def describe() -> dict:
    """Columns and row count, for the planning prompt."""
    with DATA_PATH.open() as f:
        reader = csv.reader(f)
        columns = next(reader)
        row_count = sum(1 for _ in reader)
    return {"columns": columns, "row_count": row_count}
