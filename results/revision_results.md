# Revision results (round 2): new judge families, consistency, agreement, per-class

Judge runs executed 2026-09-19 (full runs) and 2026-09-20 (six buffer re-runs +
one audit re-run) with the paper's unmodified 3-turn protocol
(`judge/eval_3turn.py --reflect base`: dossier → classify → reflect,
`TAXJUDGE_CONCURRENCY=3`), `claude-agent-sdk` 0.2.157 through the local shim to
the LiteLLM proxy (`litellm-proxy.ml-serving-internal.scale.com`, key alias
`mldg-eval-showdown`). All scoring is offline from `predictions/`. The bare
`plot/bootstrap_ci.py` sanity check reproduces the paper exactly (GPT-5.5
category κ = 0.76) in this environment.

**Every run is complete (40/40 dossiers)**, so there are no
missing-counted-as-incorrect sensitivity rows this round: after the
`max_buffer_size` fix (§9) all six previously missing dossiers were produced,
and the one dossier invalidated by the leak audit (§7) was re-run clean.

## 1. All eight judges vs. human labels — 95% bootstrap CIs (B=2000)

`plot/bootstrap_ci.py --run ...`; every row N=40, every run complete.

| Judge | run | N | Cat Acc | Cat F1 | Cat κ | Mode Acc | Mode F1 |
|---|---|---|---|---|---|---|---|
| GPT-5.5 (paper) | `gpt-5.5-xhigh_3turn_base__20260618-160352` | 40 | 0.80 [0.68, 0.93] | 0.69 [0.51, 0.83] | 0.76 [0.61, 0.90] | 0.72 [0.57, 0.85] | 0.64 [0.49, 0.76] |
| Claude-Opus-4.6 (paper) | `claude-opus-4-6_3turn_base__20260618-160352` | 40 | 0.75 [0.62, 0.88] | 0.61 [0.41, 0.75] | 0.71 [0.55, 0.85] | 0.70 [0.55, 0.82] | 0.57 [0.42, 0.72] |
| Claude-Opus-4.7 (paper) | `claude-opus-4-7_3turn_base__20260618-160352` | 40 | 0.75 [0.62, 0.88] | 0.63 [0.45, 0.76] | 0.71 [0.55, 0.85] | 0.62 [0.47, 0.78] | 0.53 [0.39, 0.65] |
| Claude-Opus-4.8 (paper) | `opus-4.8_3turn_base__20260618-224835` | 40 | 0.75 [0.62, 0.88] | 0.62 [0.46, 0.75] | 0.70 [0.54, 0.85] | 0.68 [0.53, 0.82] | 0.58 [0.44, 0.71] |
| **Gemini-3.1-Pro (new)** | `gemini-3.1-pro-max_3turn_base__20260919-062335` | 40 | **0.85 [0.72, 0.95]** | **0.84 [0.65, 0.94]** | **0.82 [0.68, 0.94]** | 0.70 [0.55, 0.82] | **0.65 [0.49, 0.74]** |
| Grok-4.6 (new) | `grok-4.6-max_3turn_base__20260919-062335` | 40 | 0.70 [0.55, 0.85] | 0.63 [0.42, 0.75] | 0.65 [0.48, 0.80] | 0.57 [0.42, 0.72] | 0.48 [0.33, 0.60] |
| GPT-6-Astra (new) | `gpt-6-astra-max_3turn_base__20260919-082408` | 40 | 0.68 [0.53, 0.80] | 0.70 [0.51, 0.76] | 0.63 [0.46, 0.78] | 0.55 [0.40, 0.70] | 0.50 [0.34, 0.58] |
| Claude-Fable-5.1 (new) | `claude-fable-5-1_3turn_base__20260919-092955` | 40 | 0.72 [0.57, 0.85] | 0.70 [0.49, 0.78] | 0.68 [0.51, 0.83] | 0.68 [0.53, 0.82] | 0.63 [0.46, 0.72] |

Gemini 3.1 Pro is the strongest single judge on every category-level metric;
its CIs overlap GPT-5.5's. GPT-6-Astra's numbers include its 4 empty verdicts
(scored as incorrect; §8). Judges from all four families land in κ 0.63–0.82
against the human labels, i.e. the taxonomy is usable well beyond the model
families that produced the paper's judges.

## 2. Missing-counted-as-incorrect sensitivity

Not applicable this round: every run reached 40/40, so the scored rows and the
missing-as-incorrect rows would be identical.

## 3. GPT-5.5 consistency across three runs (paper config, all N=40)

Mean ± sd over the three complete runs:

| | Cat Acc | Cat F1 | Cat κ | Mode Acc | Mode F1 |
|---|---|---|---|---|---|
| GPT-5.5, 3 runs | 0.80 ± 0.02 | 0.70 ± 0.02 | 0.76 ± 0.03 | 0.68 ± 0.05 | 0.57 ± 0.06 |

Run-vs-run agreement (self-consistency; every pair N=40):

| pair | category agreement | category κ | mode agreement | mode κ |
|---|---|---|---|---|
| paper run vs run 2 | 0.82 | 0.78 | 0.68 | 0.66 |
| paper run vs run 3 | 0.80 | 0.75 | 0.75 | 0.74 |
| run 2 vs run 3 | 0.90 | 0.88 | 0.80 | 0.79 |

Self-consistency (category κ 0.75–0.88) is at or above the judge's agreement
with the human labels (κ 0.76 ± 0.03): the paper's headline numbers are not a
lucky draw of one run.

## 4. Judge-vs-judge agreement (shared-priors check)

A reviewer suggested the paper's judge agreement might reflect shared model
priors, since three of four judges were Claude models. With judges from four
families (Anthropic, OpenAI, Google, xAI) this is now testable.
`plot/make_kappa_heatmap.py` (all 8 runs + human; figure at
`figures/judge-kappa-heatmap.pdf`, committed):

Category κ:

| | human | GPT-5.5 | Opus-4.6 | Opus-4.7 | Opus-4.8 | Gemini-3.1-Pro | Grok-4.6 | GPT-6-Astra | Fable-5.1 |
|---|---|---|---|---|---|---|---|---|---|
| human | — | 0.763 | 0.706 | 0.706 | 0.702 | 0.823 | 0.647 | 0.631 | 0.680 |
| GPT-5.5 | 0.763 | — | 0.755 | 0.726 | 0.751 | 0.605 | 0.600 | 0.596 | 0.639 |
| Opus-4.6 | 0.706 | 0.755 | — | 0.818 | 0.845 | 0.637 | 0.816 | 0.597 | 0.790 |
| Opus-4.7 | 0.706 | 0.726 | 0.818 | — | 0.721 | 0.699 | 0.664 | 0.594 | 0.730 |
| Opus-4.8 | 0.702 | 0.751 | 0.845 | 0.721 | — | 0.570 | 0.718 | 0.562 | 0.725 |
| Gemini-3.1-Pro | 0.823 | 0.605 | 0.637 | 0.699 | 0.570 | — | 0.696 | 0.597 | 0.702 |
| Grok-4.6 | 0.647 | 0.600 | 0.816 | 0.664 | 0.718 | 0.696 | — | 0.538 | 0.818 |
| GPT-6-Astra | 0.631 | 0.596 | 0.597 | 0.594 | 0.562 | 0.597 | 0.538 | — | 0.599 |
| Fable-5.1 | 0.680 | 0.639 | 0.790 | 0.730 | 0.725 | 0.702 | 0.818 | 0.599 | — |

Failure-mode κ (same layout):

| | human | GPT-5.5 | Opus-4.6 | Opus-4.7 | Opus-4.8 | Gemini-3.1-Pro | Grok-4.6 | GPT-6-Astra | Fable-5.1 |
|---|---|---|---|---|---|---|---|---|---|
| human | — | 0.715 | 0.689 | 0.612 | 0.663 | 0.689 | 0.560 | 0.537 | 0.663 |
| GPT-5.5 | 0.715 | — | 0.739 | 0.661 | 0.739 | 0.558 | 0.583 | 0.536 | 0.610 |
| Opus-4.6 | 0.689 | 0.739 | — | 0.738 | 0.764 | 0.557 | 0.686 | 0.510 | 0.713 |
| Opus-4.7 | 0.612 | 0.661 | 0.738 | — | 0.659 | 0.558 | 0.555 | 0.432 | 0.634 |
| Opus-4.8 | 0.663 | 0.739 | 0.764 | 0.659 | — | 0.530 | 0.658 | 0.482 | 0.686 |
| Gemini-3.1-Pro | 0.689 | 0.558 | 0.557 | 0.558 | 0.530 | — | 0.634 | 0.508 | 0.687 |
| Grok-4.6 | 0.560 | 0.583 | 0.686 | 0.555 | 0.658 | 0.634 | — | 0.456 | 0.764 |
| GPT-6-Astra | 0.537 | 0.536 | 0.510 | 0.432 | 0.482 | 0.508 | 0.456 | — | 0.534 |
| Fable-5.1 | 0.663 | 0.610 | 0.713 | 0.634 | 0.686 | 0.687 | 0.764 | 0.534 | — |

**Family means (category level):** within the Claude family (Opus 4.6/4.7/4.8,
Fable 5.1; 6 pairs) mean κ = **0.771**; across families (22 pairs) mean κ =
**0.658** (0.693 excluding GPT-6-Astra, the weakest judge overall). So
within-family agreement is somewhat higher (+0.11), consistent with some shared
priors — but the honest reading has three parts:

1. The gap is modest, and it does **not** carry the result. Every judge's κ
   with the *human* labels (0.631–0.823) is in the same range as judge-judge
   agreement, and the best human-agreement judge is Gemini — not a Claude
   model, and not the family that authored the taxonomy's original labels.
2. Cross-family pairs can agree at within-family levels: Grok-4.6 vs Opus-4.6
   (0.816) and vs Fable-5.1 (0.818) match the highest within-Claude pairs.
3. The across-family mean is dragged down mainly by GPT-6-Astra, which agrees
   weakly with *everyone* (0.538–0.599, and 0.631 with the human labels),
   i.e. a generally noisier judge rather than a family effect.

Conclusion for the reviewer: agreement among the paper's judges is not an
artifact of shared Claude priors — judges from four different families all
recover the human labels at κ 0.63–0.82, and the single best judge is from a
family that contributed no labels to the taxonomy.

## 5. Selective voting

8-judge panel (paper's 4 + all 4 new; complete runs, panel N=40):

| level | rule | coverage | precision (correct/committed) | recall (correct/N) | F1 |
|-------|------|----------|-------------------------------|--------------------|----|
| CATEGORY | 2/8 | 40/40 (1.000) | 32/40 (0.800) | 32/40 (0.800) | 0.800 (ties:2) |
| CATEGORY | 3/8 | 38/40 (0.950) | 31/38 (0.816) | 31/40 (0.775) | 0.795 |
| CATEGORY | 4/8 | 38/40 (0.950) | 31/38 (0.816) | 31/40 (0.775) | 0.795 |
| CATEGORY | 5/8 | 34/40 (0.850) | 30/34 (0.882) | 30/40 (0.750) | 0.811 |
| CATEGORY | 6/8 | 30/40 (0.750) | 28/30 (0.933) | 28/40 (0.700) | 0.800 |
| CATEGORY | 7/8 | 24/40 (0.600) | 24/24 (1.000) | 24/40 (0.600) | 0.750 |
| CATEGORY | 8/8 | 20/40 (0.500) | 20/20 (1.000) | 20/40 (0.500) | 0.667 |
| SUBTYPE | 2/8 | 40/40 (1.000) | 29/40 (0.725) | 29/40 (0.725) | 0.725 (ties:2) |
| SUBTYPE | 3/8 | 38/40 (0.950) | 28/38 (0.737) | 28/40 (0.700) | 0.718 |
| SUBTYPE | 4/8 | 38/40 (0.950) | 28/38 (0.737) | 28/40 (0.700) | 0.718 |
| SUBTYPE | 5/8 | 34/40 (0.850) | 27/34 (0.794) | 27/40 (0.675) | 0.730 |
| SUBTYPE | 6/8 | 30/40 (0.750) | 25/30 (0.833) | 25/40 (0.625) | 0.714 |
| SUBTYPE | 7/8 | 24/40 (0.600) | 23/24 (0.958) | 23/40 (0.575) | 0.719 |
| SUBTYPE | 8/8 | 20/40 (0.500) | 19/20 (0.950) | 19/40 (0.475) | 0.633 |

Caveats (as required, reported rather than hidden):
- `vote_offline.py` scores only ids every panel member has; all runs are
  complete, so panel N=40.
- An empty verdict is dropped from the tally, so on GPT-6-Astra's four
  empty-verdict ids (E2, E3, E29, E38) the effective panel is 7 judges, not 8.
  Excluding those four ids entirely (N=36), the vote barely moves — e.g.
  CATEGORY 2/8: coverage 1.000, precision 0.833, F1 0.833; 5/8: coverage
  0.889, precision 0.875, F1 0.824; 8/8: coverage 0.556, precision 1.000,
  F1 0.714. Full N=36 table in `results/vote8_excl_empty.txt`.

5-judge panel (paper's 4 + Gemini, N=40), for comparison with round 1:

| level | rule | coverage | precision | recall | F1 |
|-------|------|----------|-----------|--------|----|
| CATEGORY | 2/5 | 40/40 (1.000) | 31/40 (0.775) | 31/40 (0.775) | 0.775 (ties:1) |
| CATEGORY | 3/5 | 36/40 (0.900) | 30/36 (0.833) | 30/40 (0.750) | 0.789 |
| CATEGORY | 4/5 | 30/40 (0.750) | 29/30 (0.967) | 29/40 (0.725) | 0.829 |
| CATEGORY | 5/5 | 25/40 (0.625) | 25/25 (1.000) | 25/40 (0.625) | 0.769 |
| SUBTYPE | 2/5 | 40/40 (1.000) | 28/40 (0.700) | 28/40 (0.700) | 0.700 (ties:1) |
| SUBTYPE | 3/5 | 36/40 (0.900) | 27/36 (0.750) | 27/40 (0.675) | 0.711 |
| SUBTYPE | 4/5 | 30/40 (0.750) | 26/30 (0.867) | 26/40 (0.650) | 0.743 |
| SUBTYPE | 5/5 | 25/40 (0.625) | 23/25 (0.920) | 23/40 (0.575) | 0.708 |

Best operating points: 5-judge 4/5 (category F1 0.829, precision 0.967) and
8-judge 5/8 (F1 0.811 at higher coverage 0.850). Both beat the paper's best
4-judge ensemble (3/4: F1 0.800).

## 6. Per-class results and confusion matrices

Per-judge breakdowns: `results/per-class/<Judge>.txt`; full failure-mode
confusion matrices: `results/per-class/<Judge>-mode-confusion.csv` (Judges:
GPT-5.5, Opus-4.6, Opus-4.7, Opus-4.8, Gemini-3.1-Pro, Grok-4.6, GPT-6-Astra,
Claude-Fable-5.1).

Summary (N=40 for all):

| Judge | category classes (gold ∪ pred) | cat. support-1 | mode classes (gold ∪ pred) | mode support-1 |
|---|---|---|---|---|
| GPT-5.5 | 14 | 6/14 | 30 | 21/30 |
| Opus-4.6 | 14 | 6/14 | 30 | 21/30 |
| Opus-4.7 | 14 | 6/14 | 30 | 21/30 |
| Opus-4.8 | 14 | 6/14 | 30 | 21/30 |
| Gemini-3.1-Pro | 14 | 6/14 | 30 | 21/30 |
| Grok-4.6 | 15 | 6/15 | 31 | 21/31 |
| GPT-6-Astra | 15 | 6/15 | 34 | 21/34 |
| Claude-Fable-5.1 | 14 | 6/14 | 30 | 21/30 |

Six of the 14 gold categories and 21 of the 30 gold failure modes have exactly
one gold example, so macro-F1 is volatile at both levels — a judge that misses
one singleton class moves its macro-F1 by roughly 1/30. Note the label-set
effect the task called out: Grok and GPT-6-Astra predict classes outside the
gold set (15 and 34-class label sets), so their macro-F1 averages over more
classes than the others'. Recurring confusion pairs across judges: gold
*Under-initiative* → pred *Over-initiative* (or *Reasoning Failure*), gold
*Satisficing* → pred *Reasoning Failure*, gold *Over-initiative* → pred *Value
Misalignment*, and confusions among the *Context Following Failure* subtypes —
mostly adjacent-severity or sibling-mode mistakes rather than cross-edge errors.

## 7. Answer-key access audit (`plot/leak_audit.py`)

The judge runs behind a PreToolUse hook that denies tool calls referencing the
answer key; the audit classifies every suspicious call in every stored run by
what actually happened (WEB QUERY / DENIED / UNDECIDABLE / READ). **Final
state: all 14 runs in `predictions/` audit clean — no READ, no UNDECIDABLE.**
Per run:

| run | verdicts |
|---|---|
| `claude-fable-5-1_3turn_base__20260919-092955` | no suspicious calls |
| `claude-opus-4-6_3turn-oracle_none__20260618-161410` (paper) | 1 NO-GOLD-IN-RESULT, 2 WEB QUERY |
| `claude-opus-4-6_3turn_base__20260618-160352` (paper) | 6 NO-GOLD-IN-RESULT |
| `claude-opus-4-7_3turn-oracle_none__20260618-173357` (paper) | 2 DENIED, 1 WEB QUERY |
| `claude-opus-4-7_3turn_base__20260618-160352` (paper) | 2 WEB QUERY |
| `gemini-3.1-pro-max_3turn_base__20260919-062335` | no suspicious calls |
| `gpt-5.5-xhigh_3turn-oracle_none__20260618-142516` (paper) | 1 DENIED, 2 NO-GOLD-IN-RESULT |
| `gpt-5.5-xhigh_3turn_base__20260618-160352` (paper) | 1 DENIED |
| `gpt-5.5-xhigh_3turn_base__20260919-105038` | no suspicious calls |
| `gpt-5.5-xhigh_3turn_base__20260919-105615` | no suspicious calls |
| `gpt-6-astra-max_3turn_base__20260919-082408` | no suspicious calls |
| `grok-4.6-max_3turn_base__20260919-062335` | 1 DENIED, 2 NO-GOLD-IN-RESULT (after E32 re-run, below) |
| `opus-4.8_3turn-oracle_none__20260618-152627` (paper) | 1 WEB QUERY (E31's own transcript; expected) |
| `opus-4.8_3turn_base__20260618-224835` (paper) | no suspicious calls |

The paper's four scored runs audit clean, which is the evidence that the
reported κ values are not contaminated.

**One dossier was invalidated and re-run because of this audit.** The original
Grok E32 dossier's judge downloaded the *published paper itself*
(`arxiv.org/pdf/2607.28802`) and extracted the E32 worked-example section with
`pdftotext`; its final answer cited "Model or Harness?, worked example E32" as
a source. The audit initially marked the truncated results UNDECIDABLE; manual
inspection of the trajectory settled it as a READ (the paper's worked examples
carry the gold analysis). The dossier was deleted and E32 re-run once
(2026-09-20, run `retries/grok-4.6-max_3turn_base__20260920-043513`): the
re-run never touched the paper, worked from the primary ToolMaze sources, has
no flags, and reached the same label (model — tool, fault: model, Tool
Recovery Failure). **Protocol gap worth fixing in a future round:** the hook's
`FORBIDDEN_PATTERNS` cover local answer-key paths but not the published PDF of
the paper, which contains the same labels; the audit script catches this
post-hoc, but the hook does not prevent it.

The hook-flagged-but-harmless attempts from round 1 (Grok E1 fetching a public
`aider-swe-bench` "predictions/" URL; Grok E2 and Fable E38 grepping the
filesystem; GPT-5.5 run-3 E2/E8/E28 attempting to Read this repo's
`predictions/` and `data/examples.jsonl`) were all denied by the hook; those
dossiers were deleted and re-run clean in round 1 as a precaution.

## 8. Per-run log

All runs: 3-turn judge, `--reflect base`, `TAXJUDGE_CONCURRENCY=3`. "Params"
are the request-body extras from `ALIASES` in `judge/common.py`; each
non-Claude value is the highest reasoning effort the endpoint validates
(bogus values are rejected server-side for gpt-6-astra and Grok, by LiteLLM
for Gemini). Each run folder in `predictions/` carries its own
`manifest.json`, `run.log`, and `retries/` subfolders; `manifest.json` was
written at main-run time and intentionally not regenerated after retry merges
(dossiers are the source of truth). Cost/token totals per run: not recorded
(the judge code logs neither; the proxy reports only key-level spend — the
whole revision consumed ≈ $801 on key alias `mldg-eval-showdown`, of which
round 2 was ≈ $15).

| run | model id | params | date | dossiers | errors → resolution | leak verdicts | empty verdicts | git SHA |
|---|---|---|---|---|---|---|---|---|
| `gemini-3.1-pro-max_3turn_base__20260919-062335` | `gemini/gemini-3.1-pro-preview` | `reasoning_effort: max` | 2026-09-19 | 40/40 | none | clean | 0 | run `9044864`+aliases |
| `grok-4.6-max_3turn_base__20260919-062335` | `xai/grok-4.6` | `reasoning_effort: max` | 2026-09-19 (+2 re-runs 09-20) | 40/40 | E14, E16 buffer → E16 retried 09-19, E14 re-run after buffer fix; E32 re-run after audit | clean after E32 re-run; round-1 E1/E2 hook-denied attempts re-run clean | 0 | run `9044864`+aliases; E14/E32 dossiers at `a8fb10a` |
| `gpt-6-astra-max_3turn_base__20260919-082408` | `gpt-6-astra` | `allowed_openai_params: [reasoning]`, `reasoning.effort: max` | 2026-09-19 (+3 re-runs 09-20) | 40/40 | E10, E13, E14, E16, E32 buffer → E13/E14 retried 09-19; E10/E16/E32 re-run after buffer fix | clean | 4 (E2, E3, E29, E38; left as-is, score as incorrect) | run `9044864`+aliases; E10/E16/E32 at `a8fb10a` |
| `claude-fable-5-1_3turn_base__20260919-092955` | `claude-fable-5-1` | none (Claude ids drop extras, as the paper ran Opus) | 2026-09-19 (+1 re-run 09-20) | 40/40 | E10, E16 buffer → E10 retried 09-19; E16 re-run after buffer fix | E38 hook-denied attempt re-run clean (09-19) | 0 | run `9044864`+aliases; E16 at `a8fb10a` |
| `gpt-5.5-xhigh_3turn_base__20260919-105038` (run 2) | `gpt-5.5` | `reasoning.effort: xhigh` (paper config) | 2026-09-19 (+1 re-run 09-20) | 40/40 | E10, E25 buffer → E10 retried 09-19; E25 re-run after buffer fix | clean | 0 | run `9044864`+aliases; E25 at `a8fb10a` |
| `gpt-5.5-xhigh_3turn_base__20260919-105615` (run 3) | `gpt-5.5` | `reasoning.effort: xhigh` (paper config) | 2026-09-19 | 40/40 | none | E2/E8/E28 hook-denied attempts re-run clean (09-19) | 0 | run `9044864`+aliases |

("run `9044864`+aliases": the 09-19 runs executed with the three new `ALIASES`
entries in the working tree, committed immediately after as `574945f`; the
manifests record the base SHA `9044864`.)

No model was skipped: all four requested new judges completed 40/40.

## 9. Changes since round 1

- **`a8fb10a`** — `harness: raise SDK stdout buffer to 64 MiB`: the single
  code change that fixed every missing dossier. Round 1 lost 6 (run, id) pairs
  to `claude_agent_sdk`'s 1 MiB stdout buffer
  (`CLIJSONDecodeError: JSON message exceeded maximum buffer size of 1048576
  bytes`, deterministic per (model, example)). It is transport plumbing: no
  model, prompt, tool, or verdict-parsing change.
- **Dossiers produced after the buffer fix (2026-09-20):** Grok E14; Astra
  E10, E16, E32; Fable E16; GPT-5.5-run-2 E25 — all verified id==filename,
  non-empty verdict, no leak flags before merging.
- **Deleted and re-run because of the audit:** Grok E32 (§7). Same final
  label, clean provenance.
- `plot/make_kappa_heatmap.py`: the four new runs added to `DIRS` (the other
  sanctioned code change).
- `results/per-class/` and the committed `figures/judge-kappa-heatmap.pdf` are
  new artifacts this round.
