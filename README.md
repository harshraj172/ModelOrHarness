# Agent failure taxonomy — judge code and results

Paper: [arxiv.org/abs/2607.28802](https://arxiv.org/abs/2607.28802)

Owner: Harsh Raj (harsh.raj@scale.com)

Mentor/co-author: Vipul Gupta (vipul.gupta@scale.com)

## The paper

Most agent evals report pass/fail and stop there, which doesn't say who should fix a
failure. The paper sorts 41 failure modes by the interaction they came from: each gets
an edge (which two components were talking) and a fault side (which one's at fault).
Model-side failures need post-training, harness-side need scaffolding fixes,
environment/grader-side need eval redesign.

40 worked examples ground the categories, pulled from public benchmarks, system cards,
incident reports, and logged trajectories. Four frontier models judge those 40 examples
blind (taxonomy definitions only, no hints) to check the categories hold up outside the
authors' own labeling. Best judge: Cohen's κ = 0.76 against human labels. Judges agree
with each other about as much as they agree with the humans.

## This folder

```
judge/               3-turn judge harness + prompts
data/                40 examples with gold labels
predictions/         stored judge output the paper's numbers come from
appendix_examples/   full source for 5 examples not hosted publicly
plot/                scoring + figure scripts
REPRODUCE.md         exact commands
```

## Numbers

Full tables and the κ heatmap are in **REPRODUCE.md** — this is just a taste. Category
is the judge's (edge, fault side) label vs. the human's, e.g. "harness–model, fault:
model." Mode is the specific failure mode name within that category, a finer-grained
match. Both are F1 against the human gold label, over all 40 examples.

| Judge | Category F1 | Mode F1 |
|---|---|---|
| GPT-5.5 | 0.69 | 0.64 |
| Claude-Opus-4.6 | 0.61 | 0.57 |
| Claude-Opus-4.7 | 0.63 | 0.53 |
| Claude-Opus-4.8 | 0.62 | 0.58 |

At 3/4 judge agreement (the ensemble abstains unless 3 of the 4 judges agree on a
category, then commits to it): category F1 0.80, covering 35 of 40 examples.

**REPRODUCE.md** has the full Table 2/3 breakdown, the ensemble table at every
agreement threshold, and the exact commands to regenerate all of this from the stored
predictions. No key or network needed.

## Data-integrity notes (audit, 2026-09-02)

- `predictions/*/manifest.json` files were DELETED: their score blocks were
  stale (written mid-run at n=39) and disagreed with the dossiers on disk.
  The dossiers are the source of truth; `plot/score_tables.py` recomputes
  everything from them and matches the paper exactly.
- `predictions/opus-4.8_3turn_base__20260618-160352/` (an earlier,
  lower-scoring Opus-4.8 run superseded by `__224835`, referenced by no
  script) was removed; it survives in git history.
- KNOWN QUIRK, left as-is: `gpt-5.5-xhigh_3turn-oracle_none__20260618-142516/dossiers/`
  E12..E23 carry internal `id` fields shifted by -1 (E12.json says "E11").
  The FILENAME is authoritative -- each dossier's embedded gold matches
  `data/examples.jsonl` under its filename. That run also has 39 dossiers
  (E11 absent), which is why Table 2's GPT-5.5 gold-category column is over
  39 examples while other rows use 40.
- `gold.vulnerability` in `data/examples.jsonl` was restored 2026-09-02 from
  the paper's published Table 5 (tab:risk): 15 examples across 6 categories.
  Older dossiers carry an earlier F1-F8 coding that the paper revised during
  writing (E12/E13 re-binned to Rogue Agents; the F4 group narrowed); the
  historical codes remain readable in `predictions/*/dossiers/*.json`.
- KNOWN COUNT DRIFT: `judge/taxonomy.py` enumerates 42 (edge, mode) rows /
  38 unique mode names; the paper and this README say "41 failure modes
  (36 model, 5 non-model)". The canonical count is 41 -- taxonomy.py
  over-splits by one; reconcile before using taxonomy.py as the vocabulary
  of record.
- Figures 1-2 generators live in `figures_src/` (added 2026-09-02); see its
  README for exactness status (Fig 2 byte-identical; Fig 1 environment-
  sensitive, authoritative PDF kept in `figures_src/reference/`).
