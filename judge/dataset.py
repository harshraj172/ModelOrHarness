"""Gold dataset — read from the STATIC snapshot in data/examples.jsonl.
The snapshot is materialized from the AFT paper by sync_from_latex.py (run once"""

from __future__ import annotations

import json
from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "data" / "examples.jsonl"


def build() -> list[dict]:
    return [json.loads(ln) for ln in EXAMPLES.read_text().splitlines() if ln.strip()]


def gold_map() -> dict:
    """{id: record} keyed by example id, for scoring."""
    return {e["id"]: e for e in build()}
