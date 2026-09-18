"""Gold dataset — read from the STATIC snapshot in data/examples.jsonl.
The snapshot is materialized from the AFT paper by sync_from_latex.py (run once"""

from __future__ import annotations

import json
import os
from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "data" / "examples.jsonl"


def build() -> list[dict]:
    return [json.loads(ln) for ln in EXAMPLES.read_text().splitlines() if ln.strip()]


def gold_map() -> dict:
    """{id: record} keyed by example id, for scoring.
    If TAXJUDGE_BUNDLES is set, bundled references (appendix_examples/...) are
    rewritten to that absolute directory so the judge can open them."""
    m = {e["id"]: e for e in build()}
    bundles = os.environ.get("TAXJUDGE_BUNDLES")
    if bundles:
        for e in m.values():
            e["reference"] = e["reference"].replace("appendix_examples/", bundles.rstrip("/") + "/")
    return m
