"""Per-class results and the per-mode confusion matrix for one judge run.

Offline: reads stored dossiers only (no key, no network).

  python3 plot/per_class.py                                   # paper's GPT-5.5 run
  python3 plot/per_class.py --run predictions/<run_dir>       # any run

Category = edge|fault_side (the scored unit). Mode = failure-mode name.
Support is the number of gold examples in that class, so classes with support 1
are exactly the ones whose macro-F1 contribution is unstable.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT = "predictions/gpt-5.5-xhigh_3turn_base__20260618-160352"


def load(run: str):
    d = Path(run)
    d = d if d.is_absolute() else ROOT / d
    rows = []
    for f in sorted((d / "dossiers").glob("*.json"), key=lambda p: int(p.stem[1:])):
        x = json.loads(f.read_text())
        g, p = x["gold"], x["pred"]
        rows.append({
            "id": f.stem,
            "gc": f"{g['edge']} (fault: {g['fault_side']})",
            "pc": f"{p['edge']} (fault: {p['fault_side']})",
            "gm": g["failure_mode"],
            "pm": p["failure_mode"],
        })
    return rows


def per_class(rows, gk: str, pk: str, title: str) -> None:
    labels = sorted({r[gk] for r in rows} | {r[pk] for r in rows})
    print(f"\n{title}  (N={len(rows)}, {len(labels)} classes seen)")
    print(f"{'class':52}{'sup':>4}{'P':>7}{'R':>7}{'F1':>7}")
    for lab in labels:
        tp = sum(r[gk] == lab and r[pk] == lab for r in rows)
        fp = sum(r[pk] == lab and r[gk] != lab for r in rows)
        fn = sum(r[gk] == lab and r[pk] != lab for r in rows)
        sup = tp + fn
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / sup if sup else 0.0
        f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
        flag = "  <- support 1" if sup == 1 else ""
        print(f"{lab[:52]:52}{sup:>4}{p:>7.2f}{rc:>7.2f}{f1:>7.2f}{flag}")
    singles = sum(1 for lab in labels if sum(r[gk] == lab for r in rows) == 1)
    print(f"  classes with support 1: {singles}/{len(labels)}")


def confusions(rows, gk: str, pk: str, title: str) -> None:
    c = Counter((r[gk], r[pk]) for r in rows if r[gk] != r[pk])
    print(f"\n{title}: {sum(c.values())} errors, most frequent confusions")
    for (g, p), n in c.most_common(10):
        print(f"  {n}x  gold {g[:34]:34} -> pred {p[:34]}")


def matrix(rows, gk: str, pk: str, path: Path) -> None:
    labels = sorted({r[gk] for r in rows} | {r[pk] for r in rows})
    idx = {l: i for i, l in enumerate(labels)}
    m = defaultdict(int)
    for r in rows:
        m[(idx[r[gk]], idx[r[pk]])] += 1
    with path.open("w") as fh:
        fh.write("gold\\pred," + ",".join(labels) + "\n")
        for l in labels:
            fh.write(l + "," + ",".join(str(m[(idx[l], idx[c])]) for c in labels) + "\n")
    print(f"\nfull mode confusion matrix written to {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=DEFAULT)
    ap.add_argument("--csv", default=None, help="write the full mode confusion matrix here")
    a = ap.parse_args()
    rows = load(a.run)
    print(f"run: {a.run}")
    per_class(rows, "gc", "pc", "CATEGORY (edge, fault side)")
    per_class(rows, "gm", "pm", "FAILURE MODE")
    confusions(rows, "gc", "pc", "CATEGORY")
    confusions(rows, "gm", "pm", "FAILURE MODE")
    if a.csv:
        matrix(rows, "gm", "pm", Path(a.csv))


if __name__ == "__main__":
    main()
