"""Generate the judge inter-annotator agreement heatmap for the AFT paper.
Computes Cohen's kappa (category + subtype) among the human gold and the five judge"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
# NeurIPS requires Type 1 or embedded TrueType fonts only; matplotlib's PDF
# default (fonttype 3) emits Type 3 and would fail the submission check.
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

HERE = Path(__file__).parent
OUT = Path(__file__).parent.parent / "figures" / "judge-kappa-heatmap.pdf"

GOLD = HERE.parent / "data" / "examples.jsonl"
DIRS = {
    "GPT-5.5": HERE.parent / "predictions/gpt-5.5-xhigh_3turn_base__20260618-160352/dossiers",
    "Opus-4.6": HERE.parent / "predictions/claude-opus-4-6_3turn_base__20260618-160352/dossiers",
    "Opus-4.7": HERE.parent / "predictions/claude-opus-4-7_3turn_base__20260618-160352/dossiers",
    "Opus-4.8": HERE.parent / "predictions/opus-4.8_3turn_base__20260618-224835/dossiers",
}
RATERS = ["human", *DIRS]


def norm(s: str) -> str:
    s = str(s).lower().replace("lead-agent","orchestrator").replace("lead agent","orchestrator")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    la = [a for a, _ in pairs]
    lb = [b for _, b in pairs]
    labels = set(la) | set(lb)
    pe = sum((la.count(x) / n) * (lb.count(x) / n) for x in labels)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def main() -> None:
    gold = {json.loads(line)["id"]: json.loads(line) for line in GOLD.read_text().splitlines() if line.strip()}
    ids = sorted(gold, key=lambda x: int(x[1:]))

    cat: dict[str, dict[str, str]] = {}
    sub: dict[str, dict[str, str]] = {}
    cat["human"] = {i: norm(f"{gold[i]['gold']['edge']} (fault: {gold[i]['gold']['fault_side']})") for i in ids}
    sub["human"] = {i: norm(gold[i]["gold"]["edge"]+"|"+gold[i]["gold"]["fault_side"]+"|"+gold[i]["gold"]["failure_mode"]) for i in ids}
    for name, d in DIRS.items():
        cat[name], sub[name] = {}, {}
        for i in ids:
            p = json.loads((d / f"{i}.json").read_text())["pred"]
            cat[name][i] = norm(p["category"])
            sub[name][i] = norm(p.get("edge","")+"|"+p.get("fault_side","")+"|"+p.get("failure_mode",""))

    def matrix(lab: dict) -> np.ndarray:
        m = np.full((len(RATERS), len(RATERS)), np.nan)
        for r, a in enumerate(RATERS):
            for c, b in enumerate(RATERS):
                if a != b:
                    m[r, c] = cohen_kappa([(lab[a][i], lab[b][i]) for i in ids])
        return m

    mats = {"Category $\\kappa$": matrix(cat), "Failure mode $\\kappa$": matrix(sub)}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    cmap = plt.cm.YlGnBu
    cmap.set_bad("0.92")
    vmin, vmax = 0.25, 0.85
    for ax, (title, M) in zip(axes, mats.items()):
        im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
        ax.set_xticks(range(len(RATERS)))
        ax.set_yticks(range(len(RATERS)))
        ax.set_xticklabels(RATERS, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(RATERS, fontsize=9)
        ax.set_title(title, fontsize=12)
        for r in range(len(RATERS)):
            for c in range(len(RATERS)):
                if r == c:
                    ax.text(c, r, "—", ha="center", va="center", color="0.5", fontsize=10)
                else:
                    v = M[r, c]
                    ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=8.5,
                            color="white" if v > 0.6 else "black")
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks(np.arange(-.5, len(RATERS), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(RATERS), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.5)
        ax.tick_params(which="both", length=0)
        n = len(RATERS)
        for xy, w, h in (((-.5, -.5), 1, n), ((-.5, -.5), n, 1)):
            ax.add_patch(Rectangle(xy, w, h, fill=False, edgecolor="black",
                                   linewidth=1.6, zorder=5, clip_on=False))
    cbar = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cbar.set_label("Cohen's $\\kappa$", fontsize=10)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")
    for title, M in mats.items():
        print(title)
        print("        " + " ".join(f"{r:>8}" for r in RATERS))
        for i, a in enumerate(RATERS):
            print(f"{a:>8} " + " ".join("    —   " if np.isnan(M[i, j]) else f"{M[i, j]:7.3f}" for j in range(len(RATERS))))


if __name__ == "__main__":
    main()
