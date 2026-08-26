"""The chat model behind the two model calls."""

from __future__ import annotations

import json
from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage

from app.config import settings

OFFLINE_PLAN = {
    "title": "Q2 order performance",
    "sections": [
        {"name": "revenue_by_region",
         "question": "Which regions produced the most revenue?"},
        {"name": "revenue_by_channel",
         "question": "Which acquisition channels produced the most revenue?"},
        {"name": "top_categories",
         "question": "Which product categories sold best?"},
        {"name": "refund_rate",
         "question": "What share of orders was refunded?"},
        {"name": "monthly_trend",
         "question": "How did revenue move month over month?"},
    ],
}

OFFLINE_CODE = '''\
import csv, json, os
from collections import defaultdict

rows = list(csv.DictReader(open(os.environ["FLYRANK_DATA"])))

by_region = defaultdict(float)
by_channel = defaultdict(float)
by_category = defaultdict(float)
by_month = defaultdict(float)
refunded = 0

for r in rows:
    revenue = float(r["revenue"])
    by_region[r["region"]] += revenue
    by_channel[r["channel"]] += revenue
    by_category[r["category"]] += revenue
    by_month[r["order_date"][:7]] += revenue
    if r["refunded"] == "true":
        refunded += 1

def ranked(d):
    return {k: round(v, 2) for k, v in sorted(d.items(), key=lambda kv: -kv[1])}

print(json.dumps({
    "revenue_by_region": ranked(by_region),
    "revenue_by_channel": ranked(by_channel),
    "top_categories": ranked(by_category),
    "refund_rate": {
        "refunded_orders": refunded,
        "total_orders": len(rows),
        "rate_pct": round(100 * refunded / len(rows), 2),
    },
    "monthly_trend": {k: round(v, 2) for k, v in sorted(by_month.items())},
}))
'''


OFFLINE_FAILING_CODE = {
    "oom": '''\
import os

print("trace", os.environ.get("FLYRANK_TRACE_ID"), flush=True)

# Grows until the container's memory ceiling kills the process. Each chunk is
# written to, not just reserved, so the pages are really faulted in.
chunks = []
while True:
    block = bytearray(8 * 1024 * 1024)
    block[::4096] = b"x" * len(block[::4096])
    chunks.append(block)
''',
    "segfault": '''\
import ctypes, os

print("trace", os.environ.get("FLYRANK_TRACE_ID"), flush=True)

# Reading address zero. The interpreter takes SIGSEGV and the container exits 139.
ctypes.string_at(0)
''',
}


class OfflineChatModel(SimpleChatModel):
    """A stand-in model with no randomness and no network."""

    @property
    def _llm_type(self) -> str:
        return "flyrank-offline-deterministic"

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        system = next(
            (m.content for m in messages if m.type == "system"), ""
        )
        if "Python scripts" not in system:
            return json.dumps(OFFLINE_PLAN)

        user = "".join(str(m.content) for m in messages if m.type == "human")
        if "without bound" in user:
            return OFFLINE_FAILING_CODE["oom"]
        if "null pointer" in user:
            return OFFLINE_FAILING_CODE["segfault"]
        return OFFLINE_CODE


def get_chat_model() -> BaseChatModel:
    if not settings.llm_is_live:
        return OfflineChatModel()

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
