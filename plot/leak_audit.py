"""Audit judge runs for answer-key access.

Offline: reads stored dossiers only (no key, no network).

  python3 plot/leak_audit.py                          # every run in predictions/
  python3 plot/leak_audit.py --run predictions/<dir>  # one run
  python3 plot/leak_audit.py --verbose                # print each flagged step

The judge runs with a PreToolUse hook that denies tool calls whose input matches
the answer-key patterns in judge/common.py. This script checks what actually
happened, per example:

  WEB QUERY    a web search/fetch that merely mentions the taxonomy in its query
               text and names no local path: cannot read the answer key
  DENIED       a suspicious tool call whose result carries the hook's refusal
  UNDECIDABLE  a suspicious tool call whose result is missing or was truncated
               when the trajectory was recorded (previews are cut at 2000 chars)
  READ         a suspicious tool call whose result came back and looks like gold
               data (edge / fault_side / failure_mode fields)

A run is clean only if it has no READ and no UNDECIDABLE. E31's own bundled
transcript mentions the taxonomy, so hits on E31 are reported separately and are
expected; they are not evidence that the answer key was read.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Paths/filenames that would reveal gold labels if a judge opened them.
SUSPECT = re.compile(
    r"examples\.jsonl|splits\.json|predictions[/\\]|judge[/\\]taxonomy\.py|"
    r"agent.{0,3}failure.{0,3}taxonomy|ModelOrHarness",
    re.I,
)
# The hook's refusal text (judge/judge_3turn.py) and generic permission errors.
DENIAL = re.compile(r"Blocked:|answer key and is off-limits|permission.{0,20}denied", re.I)
# Gold-label shape: a dossier/example record carries all three fields.
GOLD_SHAPE = re.compile(r"fault_side|failure_mode", re.I)
TRUNCATED = 2000  # _block_entry caps tool_use input and tool_result preview here


def classify(steps: list[dict]) -> list[dict]:
    """Pair each suspicious tool_use with the next tool_result (no ids are
    recorded, so pairing is positional) and classify the outcome."""
    out = []
    for i, st in enumerate(steps):
        if st.get("type") != "tool_use":
            continue
        blob = json.dumps(st, ensure_ascii=False)
        if not SUSPECT.search(blob):
            continue
        tool = str(st.get("name", ""))
        inp = str(st.get("input", ""))
        local = re.search(r"examples\.jsonl|splits\.json|predictions[/\\]|taxonomy\.py|/mnt/|/home/|\.\./|ModelOrHarness", inp, re.I)
        if tool in ("WebSearch", "WebFetch") and not local:
            out.append({"verdict": "WEB QUERY (no local path)", "tool": tool,
                        "input": inp[:300], "result": ""})
            continue
        result = next((s for s in steps[i + 1:] if s.get("type") == "tool_result"), None)
        if result is None:
            verdict = "UNDECIDABLE"
        else:
            rblob = json.dumps(result, ensure_ascii=False)
            preview = str(result.get("preview", ""))
            if DENIAL.search(rblob):
                verdict = "DENIED"
            elif GOLD_SHAPE.search(preview):
                verdict = "READ"
            elif len(preview) >= TRUNCATED:
                verdict = "UNDECIDABLE"
            else:
                verdict = "DENIED" if result.get("is_error") else "NO GOLD IN RESULT"
        out.append({"verdict": verdict, "tool": st.get("name", "?"),
                    "input": str(st.get("input", ""))[:300],
                    "result": str((result or {}).get("preview", ""))[:300]})
    return out


def audit(run: Path, verbose: bool) -> dict:
    counts: dict[str, int] = {}
    flagged: dict[str, list] = {}
    for f in sorted((run / "dossiers").glob("*.json"), key=lambda p: int(p.stem[1:])):
        d = json.loads(f.read_text())
        hits = classify(d.get("trajectory", []))
        if d.get("leaks"):
            counts["hook-flagged dossiers"] = counts.get("hook-flagged dossiers", 0) + 1
        if not hits:
            continue
        flagged[f.stem] = hits
        for h in hits:
            counts[h["verdict"]] = counts.get(h["verdict"], 0) + 1
    print(f"\n=== {run.name}  ({len(list((run / 'dossiers').glob('*.json')))} dossiers)")
    if not flagged:
        print("  no tool call referenced the answer key")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    e31 = {k: v for k, v in flagged.items() if k == "E31"}
    other = {k: v for k, v in flagged.items() if k != "E31"}
    if e31:
        print(f"  E31: {len(e31['E31'])} hit(s) — expected, its own transcript mentions the taxonomy")
    bad = {k: [h for h in v if h["verdict"] in ("READ", "UNDECIDABLE")] for k, v in other.items()}
    bad = {k: v for k, v in bad.items() if v}
    print(f"  ids needing review: {', '.join(sorted(bad)) if bad else 'none'}")
    if verbose:
        for i, hits in sorted(other.items()):
            for h in hits:
                print(f"    {i} [{h['verdict']}] {h['tool']}: {h['input'][:160]}")
                print(f"        -> {h['result'][:160]}")
    return {"run": run.name, "counts": counts, "review": sorted(bad)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", help="run dir (default: every run in predictions/)")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    runs = [Path(r) if Path(r).is_absolute() else ROOT / r for r in a.run] if a.run \
        else sorted(p for p in (ROOT / "predictions").iterdir() if (p / "dossiers").is_dir())
    if not runs:
        raise SystemExit("no runs found")
    summary = [audit(r, a.verbose) for r in runs]
    need = [s["run"] for s in summary if s["review"]]
    print("\n" + "=" * 60)
    print(f"runs audited: {len(summary)}; needing review: {len(need)}")
    for s in summary:
        if s["review"]:
            print(f"  {s['run']}: {', '.join(s['review'])}")
    print("A run is clean only if it has no READ and no UNDECIDABLE verdicts above.")


if __name__ == "__main__":
    main()
