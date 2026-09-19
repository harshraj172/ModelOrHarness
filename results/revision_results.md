# Revision results: new judge families + GPT-5.5 consistency

Runs executed 2026-09-19 against the paper's unmodified 3-turn protocol
(`judge/eval_3turn.py --reflect base`: dossier → classify → reflect,
`TAXJUDGE_CONCURRENCY=3`). Code SHA for all runs: `574945f` (branch
`revision-judges`; the only code change vs. `main` is three new `ALIASES`
entries in `judge/common.py`). Judge harness: `claude-agent-sdk` 0.2.157,
Claude Code CLI via the local shim to the LiteLLM proxy
(`litellm-proxy.ml-serving-internal.scale.com`), key alias
`mldg-eval-showdown`. Scoring is offline from `predictions/`
(`plot/bootstrap_ci.py`, `plot/vote_offline.py`); the bare
`plot/bootstrap_ci.py` sanity check reproduced Table 2 exactly
(GPT-5.5 category κ = 0.76) before any new run was scored.

**Complete runs (40/40 dossiers) are scored; incomplete runs are reported but
excluded from every table**, per the revision protocol. Three of the four new
judges are incomplete for the same deterministic harness reason (§4).

## 1. Per-judge agreement with human labels, 95% bootstrap CIs (B=2000)

`python3 plot/bootstrap_ci.py --run ...` over the complete runs (N=40 each):

| Judge | run | Cat Acc | Cat F1 | Cat κ | Mode Acc | Mode F1 |
|---|---|---|---|---|---|---|
| GPT-5.5 (paper) | `gpt-5.5-xhigh_3turn_base__20260618-160352` | 0.80 [0.68, 0.93] | 0.69 [0.51, 0.83] | 0.76 [0.61, 0.90] | 0.72 [0.57, 0.85] | 0.64 [0.49, 0.76] |
| GPT-5.5 (new, run 3) | `gpt-5.5-xhigh_3turn_base__20260919-105615` | 0.82 [0.70, 0.93] | 0.72 [0.55, 0.83] | 0.79 [0.64, 0.91] | 0.68 [0.53, 0.80] | 0.55 [0.42, 0.68] |
| Claude-Opus-4.6 (paper) | `claude-opus-4-6_3turn_base__20260618-160352` | 0.75 [0.62, 0.88] | 0.61 [0.41, 0.75] | 0.71 [0.55, 0.85] | 0.70 [0.55, 0.82] | 0.57 [0.42, 0.72] |
| Claude-Opus-4.7 (paper) | `claude-opus-4-7_3turn_base__20260618-160352` | 0.75 [0.62, 0.88] | 0.63 [0.45, 0.76] | 0.71 [0.55, 0.85] | 0.62 [0.47, 0.78] | 0.53 [0.39, 0.65] |
| Claude-Opus-4.8 (paper) | `opus-4.8_3turn_base__20260618-224835` | 0.75 [0.62, 0.88] | 0.62 [0.46, 0.75] | 0.70 [0.54, 0.85] | 0.68 [0.53, 0.82] | 0.58 [0.44, 0.71] |
| **Gemini-3.1-Pro (new)** | `gemini-3.1-pro-max_3turn_base__20260919-062335` | **0.85 [0.72, 0.95]** | **0.84 [0.65, 0.94]** | **0.82 [0.68, 0.94]** | 0.70 [0.55, 0.82] | **0.65 [0.49, 0.74]** |

Gemini 3.1 Pro is the strongest single judge observed to date on every
category-level metric, with CIs overlapping GPT-5.5's.

## 2. GPT-5.5 consistency across repeated runs

Paper config (`gpt-5.5-xhigh`, reflect=base) run twice more. Run 2 finished at
39/40 (§4), so gold-scored aggregates use the two complete runs; pairwise
agreement is over shared examples and includes run 2 with N stated.

Mean ± sd over the two complete runs (paper run + new run 3):

| | Cat Acc | Cat F1 | Cat κ | Mode Acc | Mode F1 |
|---|---|---|---|---|---|
| GPT-5.5, 2 complete runs | 0.81 ± 0.02 | 0.70 ± 0.02 | 0.78 ± 0.02 | 0.70 ± 0.04 | 0.59 ± 0.07 |

Run-vs-run category agreement (self-consistency, shared examples):

| pair | agreement | κ | N |
|---|---|---|---|
| paper run vs new run 2 | 0.85 | 0.81 | 39 |
| paper run vs new run 3 | 0.80 | 0.75 | 40 |
| new run 2 vs new run 3 | 0.90 | 0.87 | 39 |

All pairwise κ are in 0.75–0.87 — the judge agrees with itself about as much
as it agrees with the human labels (κ = 0.76–0.79), i.e. the paper's numbers
are not a lucky sample of one run.

## 3. Selective-voting ensemble

`plot/vote_offline.py` over the paper's 4 judges plus Gemini 3.1 Pro (the one
complete new run; the panel intersects ids, so including incomplete runs would
silently shrink N — they are excluded). N=40.

| level | rule | coverage | precision (correct/committed) | recall (correct/N) | F1 |
|-------|------|----------|-------------------------------|--------------------|----|
| CATEGORY | 2/5 | 40/40 (1.000) | 31/40 (0.775) | 31/40 (0.775) | 0.775 (ties:1) |
| CATEGORY | 3/5 | 36/40 (0.900) | 30/36 (0.833) | 30/40 (0.750) | 0.789 |
| CATEGORY | 4/5 | 30/40 (0.750) | 29/30 (0.967) | 29/40 (0.725) | 0.829 |
| CATEGORY | 5/5 | 25/40 (0.625) | 25/25 (1.000) | 25/40 (0.625) | 0.769 |
| SUBTYPE | 2/5 | 40/40 (1.000) | 28/40 (0.700) | 28/40 (0.700) | 0.700 (ties:1) |
| SUBTYPE | 3/5 | 36/40 (0.900) | 27/36 (0.750) | 27/40 (0.675) | 0.711 |
| SUBTYPE | 4/5 | 30/40 (0.750) | 26/30 (0.867) | 26/40 (0.650) | 0.743 |
| SUBTYPE | 5/5 | 25/40 (0.625) | 23/25 (0.920) | 23/40 (0.575) | 0.708 |

At 4/5 agreement the ensemble reaches category F1 0.829 with 96.7% precision
on committed examples — above the paper's best 3/4 ensemble (F1 0.800).

## 4. Run log: models, parameters, errors, leaks, empty verdicts

All runs: 3-turn judge, `--reflect base`, git SHA `574945f`, date 2026-09-19.
Model ids and request parameters were verified against the proxy before
running; each non-Claude alias sets the highest reasoning effort the endpoint
validates (a bogus value is rejected by the respective API, so acceptance of
`max` is meaningful for gpt-6-astra and Grok; Gemini's values are validated by
LiteLLM).

| run folder | model id | params | dossiers | errors (final missing) | leak flags | empty verdicts |
|---|---|---|---|---|---|---|
| `gemini-3.1-pro-max_3turn_base__20260919-062335` | `gemini/gemini-3.1-pro-preview` | `reasoning_effort: max` | **40/40** | 0 | 0 | 0 |
| `grok-4.6-max_3turn_base__20260919-062335` | `xai/grok-4.6` | `reasoning_effort: max` | 39/40 | E14, E16 (retry recovered E16; **E14 missing**) | E1, E2 (blocked attempts; deleted, re-run clean) | 0 |
| `gpt-6-astra-max_3turn_base__20260919-082408` | `gpt-6-astra` | `reasoning.effort: max` (via `allowed_openai_params`) | 37/40 | E10, E13, E14, E16, E32 (retry recovered E13, E14; **E10, E16, E32 missing**) | 0 | 4 (E2, E3, E29, E38) |
| `claude-fable-5-1_3turn_base__20260919-092955` | `claude-fable-5-1` | none (Claude ids drop extras, as in the paper's Opus runs) | 39/40 | E10, E16 (retry recovered E10; **E16 missing**) | E38 (blocked attempt; deleted, re-run clean) | 0 |
| `gpt-5.5-xhigh_3turn_base__20260919-105038` (run 2) | `gpt-5.5` | `reasoning.effort: xhigh` (paper config) | 39/40 | E10, E25 (retry recovered E10; **E25 missing**) | 0 | 0 |
| `gpt-5.5-xhigh_3turn_base__20260919-105615` (run 3) | `gpt-5.5` | `reasoning.effort: xhigh` (paper config) | **40/40** | 0 | E2, E8, E28 (blocked attempts; deleted, re-run clean) | 0 |

Each run folder carries its retry run under `retries/`; merged dossiers are the
source of truth and `manifest.json` was intentionally not regenerated.

**The single cause of every missing dossier** is a harness (SDK) limit, not a
model or key failure: `claude_agent_sdk` 0.2.157 aborts a session with
`CLIJSONDecodeError: Failed to decode JSON: JSON message exceeded maximum
buffer size of 1048576 bytes` when one CLI message (typically a very large
tool result on the oversized-source examples E10/E14/E16/E25/E32) exceeds its
1 MiB stdout buffer. It is deterministic per (model, example): every retry
failed identically, so per protocol retries stopped after one attempt. No
model was skipped outright — all four new judges ran; Grok, gpt-6-astra and
Fable 5.1 are reported here but excluded from §1–§3 because they are
incomplete. Raising the SDK's `max_buffer_size` (one option in
`ClaudeAgentOptions`) and re-running the 5 missing (model, example) pairs
would make all runs complete; this was proposed and deliberately not done for
this revision to keep the judge code byte-identical to the paper's.

**Leak flags.** Every flagged tool call was an *attempt* that the PreToolUse
hook denied before execution (the flags record the attempted input, not a
successful read): Grok E1 tried to WebFetch a public `aider-swe-bench`
`predictions/` URL (pattern collision with the block list); Grok E2 and
Fable E38 tried to search `/mnt/efs` for source traces; GPT-5.5 run-3
E2/E8/E28 tried to Read this repo's `predictions/` and `data/examples.jsonl`.
All flagged dossiers were deleted and re-run once; every re-run came back
clean. E31's known benign self-flag (its own transcript mentions the taxonomy)
did not occur in any run.

**Empty verdicts** (unparseable final JSON even after the sonnet repair pass)
occurred only in the gpt-6-astra run (4/37); they are left as-is and would
score as incorrect.
