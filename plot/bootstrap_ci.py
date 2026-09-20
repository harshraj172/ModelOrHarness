"""95% bootstrap CIs for judge scores, plus run-to-run consistency.

Offline: scores stored dossiers only (no key, no network).

  python3 plot/bootstrap_ci.py                       # the paper's 4 judges
  python3 plot/bootstrap_ci.py --run GPT-5.5=predictions/<dir> --run GPT-5.5=predictions/<dir2>

Repeat a name to group several runs of the same judge: the script then also
prints mean +- sd across runs and run-vs-run Cohen's kappa (self-consistency).
Scoring matches plot/score_tables.py: category = edge|fault_side,
mode = edge|fault_side|failure_mode; macro-F1 over labels seen in gold or pred.
"""

from __future__ import annotations

import argparse
import itertools
import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).parent.parent

PAPER_RUNS = [
    ("GPT-5.5", "predictions/gpt-5.5-xhigh_3turn_base__20260618-160352"),
    ("Claude-Opus-4.6", "predictions/claude-opus-4-6_3turn_base__20260618-160352"),
    ("Claude-Opus-4.7", "predictions/claude-opus-4-7_3turn_base__20260618-160352"),
    ("Claude-Opus-4.8", "predictions/opus-4.8_3turn_base__20260618-224835"),
]


def gold_rows() -> dict[str, dict]:
    """Gold labels for every test id, from data/examples.jsonl + data/splits.json."""
    ex = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data" / "examples.jsonl").read_text().splitlines() if l.strip()}
    ids = json.loads((ROOT / "data" / "splits.json").read_text())["test"]
    return {i: ex[i]["gold"] for i in ids if i in ex}


def load(run_dir: str, missing_wrong: bool = False) -> dict[str, dict]:
    """{example id (from filename, which is authoritative): {gold, pred}}
    With missing_wrong, ids absent from the run are added with a sentinel
    prediction, so an incomplete run is scored as if it got them wrong."""
    d = Path(run_dir)
    d = d if d.is_absolute() else ROOT / d
    out = {}
    for f in (d / "dossiers").glob("*.json"):
        x = json.loads(f.read_text())
        g, p = x["gold"], x["pred"]
        out[f.stem] = {
            "gc": f"{g['edge']}|{g['fault_side']}",
            "pc": f"{p['edge']}|{p['fault_side']}",
            "gm": f"{g['edge']}|{g['fault_side']}|{g['failure_mode']}",
            "pm": f"{p['edge']}|{p['fault_side']}|{p['failure_mode']}",
        }
    if missing_wrong:
        for i, g in gold_rows().items():
            if i not in out:
                gc = f"{g['edge']}|{g['fault_side']}"
                out[i] = {"gc": gc, "pc": "(missing)",
                          "gm": f"{gc}|{g['failure_mode']}", "pm": "(missing)"}
    return out


def metrics(rows: list[dict]) -> np.ndarray:
    gc, pc = [r["gc"] for r in rows], [r["pc"] for r in rows]
    gm, pm = [r["gm"] for r in rows], [r["pm"] for r in rows]
    macro = lambda a, b: f1_score(a, b, average="macro", zero_division=0)
    kappa = cohen_kappa_score(gc, pc) if len(set(gc) | set(pc)) > 1 else 1.0
    return np.array([accuracy_score(gc, pc), macro(gc, pc), kappa,
                     accuracy_score(gm, pm), macro(gm, pm)])


NAMES = ["Cat Acc", "Cat F1", "Cat kappa", "Mode Acc", "Mode F1"]


def bootstrap(rows: list[dict], b: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = len(rows)
    samples = np.array([metrics([rows[i] for i in rng.integers(0, n, n)]) for _ in range(b)])
    return metrics(rows), np.percentile(samples, 2.5, axis=0), np.percentile(samples, 97.5, axis=0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", help="Name=path/to/run_dir (repeatable; repeat a Name for multiple runs)")
    ap.add_argument("--b", type=int, default=2000, help="bootstrap resamples (default 2000)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--missing-wrong", action="store_true",
                    help="score ids missing from a run as incorrect (for incomplete runs)")
    a = ap.parse_args()
    runs = [tuple(s.split("=", 1)) for s in a.run] if a.run else PAPER_RUNS

    print(f"95% percentile bootstrap over examples, B={a.b}\n")
    print(f"{'Judge':18}{'run':44}{'N':>4}  " + "  ".join(f"{n:>20}" for n in NAMES))
    by_judge: dict[str, list[tuple[str, dict, np.ndarray]]] = defaultdict(list)
    for name, path in runs:
        data = load(path, a.missing_wrong)
        rows = [data[k] for k in sorted(data, key=lambda s: int(s[1:]))]
        point, lo, hi = bootstrap(rows, a.b, a.seed)
        by_judge[name].append((path, data, point))
        cells = "  ".join(f"{p:.2f} [{l:.2f}, {h:.2f}]".rjust(20) for p, l, h in zip(point, lo, hi))
        print(f"{name:18}{Path(path).name[:42]:44}{len(rows):>4}  {cells}")

    multi = {k: v for k, v in by_judge.items() if len(v) > 1}
    if multi:
        print("\nAcross repeated runs of the same judge (mean +- sd over runs):")
        for name, rs in multi.items():
            pts = np.array([p for _, _, p in rs])
            cells = "  ".join(f"{m:.2f} +- {s:.2f}".rjust(20) for m, s in zip(pts.mean(0), pts.std(0, ddof=1)))
            print(f"{name:18}{f'{len(rs)} runs':44}{'':>4}  {cells}")
        print("\nRun-vs-run agreement on category (self-consistency, shared examples):")
        for name, rs in multi.items():
            for (pa, da, _), (pb, db, _) in itertools.combinations(rs, 2):
                ids = sorted(set(da) & set(db))
                ya, yb = [da[i]["pc"] for i in ids], [db[i]["pc"] for i in ids]
                agree = np.mean([x == y for x, y in zip(ya, yb)])
                print(f"  {name}: {Path(pa).name} vs {Path(pb).name}: "
                      f"agreement {agree:.2f}, kappa {cohen_kappa_score(ya, yb):.2f} (N={len(ids)})")


if __name__ == "__main__":
    main()
