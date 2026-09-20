# CLAUDE-2.md: round 2 of the ARR revision runs

Round 1 is done: six new judge runs and `results/revision_results.md` on branch
`revision-judges`. This file is the remaining work. `CLAUDE.md` still holds the setup
(`.env`, `set -a; . ./.env; set +a`, bundles, model access check) and the protocol rules
(paper config `--reflect base`, one retry per id, at most 2 runs at a time, don't edit
`data/`, `judge/prompts/`, `judge/taxonomy.py`). Read it first, then do the tasks below in
order. If anything can't be followed, stop and ask the user.

Round 1 left four gaps: the runs were never pushed, three judges are incomplete and so
were left unscored, per-class results and the confusion matrix were never produced, and
the answer-key access attempts were never audited. Tasks 1–5 close all four.

## Task 1: push what already exists

```
git push -u origin revision-judges
```

The branch must contain the six new run folders under `predictions/` and
`results/revision_results.md`. Never push to `main`, and never commit `.env`. If a run
folder is missing from git because of an ignore rule, add it explicitly (`git add -f`).
Confirm afterwards with `git show --stat HEAD` that the dossiers are in.

## Task 2: audit the answer-key attempts (no API calls)

In round 1, three GPT-5.5 examples (E2, E8, E28) and three others (Grok E1, E2; Fable
E38) recorded blocked attempts to reach the answer key. The `PreToolUse` hook denies a
tool call only when its input matches the patterns in `judge/common.py`; a call that
builds the path differently would not be caught. Audit every new run:

```
python3 - <<'EOF'
import json, glob, re
PAT = re.compile(r"examples\.jsonl|splits\.json|predictions/|ModelOrHarness|appendix_examples|agent.{0,3}failure.{0,3}taxonomy|fault_side|failure_mode", re.I)
for run in sorted(glob.glob("predictions/*_3turn_base__20260919-*")):
    hits = []
    for f in sorted(glob.glob(run + "/dossiers/*.json")):
        d = json.load(open(f))
        for step in d.get("trajectory", []):
            blob = json.dumps(step)
            if PAT.search(blob):
                hits.append((f.split("/")[-1][:-5], step.get("type"), blob[:200]))
    print(f"\n=== {run}: {len(hits)} suspicious steps")
    for h in hits[:40]:
        print("  ", h)
EOF
```

For every hit decide, from the recorded step, whether it was **denied** (a `tool_result`
carrying the hook's "Blocked:" reason or `is_error`) or whether content came back. Gold
labels in the repo look like `"edge"`, `"fault_side"`, `"failure_mode"` inside a JSON
line per example.

- Any dossier where the answer key was actually read is invalid: delete it, re-run that id
  once, and say so in the results file.
- Report a table: run, ids with hits, what was attempted, denied or read.
- Also report explicitly that the audit found nothing for the runs that come out clean.
  This is the evidence that the reported κ values are not contaminated.

## Task 3: finish the incomplete runs

All missing dossiers come from one harness limit: `claude_agent_sdk` aborts a session
with `CLIJSONDecodeError: Failed to decode JSON: JSON message exceeded maximum buffer
size of 1048576 bytes` when a single CLI message exceeds 1 MiB. `ClaudeAgentOptions`
accepts `max_buffer_size`, so raise it.

1. In `judge/judge_3turn.py`, in the `ClaudeAgentOptions(...)` call inside `label()`, add:

   ```python
   max_buffer_size=64 * 1024 * 1024,
   ```

2. Commit that on its own so it is auditable, e.g. "harness: raise SDK stdout buffer to
   64 MiB (no change to prompts or judge logic)". This is transport plumbing: it does not
   change the model, the prompts, the tools, or the verdict parsing.
3. Re-run only the missing (run, id) pairs, with each run's original model/alias and
   `--reflect base`:

   | run folder | model / alias | ids to re-run |
   |---|---|---|
   | `grok-4.6-max_3turn_base__20260919-062335` | `grok-4.6-max` | E14 |
   | `gpt-6-astra-max_3turn_base__20260919-082408` | `gpt-6-astra-max` | E10, E16, E32 |
   | `claude-fable-5-1_3turn_base__20260919-092955` | `claude-fable-5-1` | E16 |
   | `gpt-5.5-xhigh_3turn_base__20260919-105038` (run 2) | `gpt-5.5-xhigh` | E25 |

   (Six pairs in total; round 1's note said five.)

4. Copy each new dossier into that run's `dossiers/` in both `judge/runs/` and
   `predictions/`, and move the re-run's folder under the run's `retries/`. Do not
   regenerate `manifest.json`.
5. One attempt per id. If the buffer change doesn't fix an id, report the new error and
   stop; don't try again.
6. Leave the 4 empty verdicts in the gpt-6-astra run (E2, E3, E29, E38) as they are. They
   score as incorrect. Say so in the results file.

## Task 4: rescore everything

All offline from `predictions/`. Run the sanity check first; it must reproduce the paper
(GPT-5.5 category κ = 0.76).

```
python3 plot/bootstrap_ci.py
```

**Every judge, with CIs.** Include the incomplete runs this time, and state N per row:

```
python3 plot/bootstrap_ci.py \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260618-160352 \
  --run Claude-Opus-4.6=predictions/claude-opus-4-6_3turn_base__20260618-160352 \
  --run Claude-Opus-4.7=predictions/claude-opus-4-7_3turn_base__20260618-160352 \
  --run Claude-Opus-4.8=predictions/opus-4.8_3turn_base__20260618-224835 \
  --run Gemini-3.1-Pro=predictions/gemini-3.1-pro-max_3turn_base__20260919-062335 \
  --run Grok-4.6=predictions/grok-4.6-max_3turn_base__20260919-062335 \
  --run GPT-6-Astra=predictions/gpt-6-astra-max_3turn_base__20260919-082408 \
  --run Claude-Fable-5.1=predictions/claude-fable-5-1_3turn_base__20260919-092955
```

**For any run still below 40/40**, run the same command again with `--missing-wrong` and
report both rows: scored-on-what-exists (with N) and missing-counted-as-incorrect (N=40).
That way nobody can read the score as the result of dropping hard examples.

**GPT-5.5 consistency** (three runs; repeating the name groups them, which prints mean ±
sd and run-vs-run κ):

```
python3 plot/bootstrap_ci.py \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260618-160352 \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260919-105038 \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260919-105615
```

**Selective voting**, paper's 4 judges plus the 4 new ones:

```
python3 plot/vote_offline.py \
  --dir GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260618-160352/dossiers \
  --dir Opus-4.6=predictions/claude-opus-4-6_3turn_base__20260618-160352/dossiers \
  --dir Opus-4.7=predictions/claude-opus-4-7_3turn_base__20260618-160352/dossiers \
  --dir Opus-4.8=predictions/opus-4.8_3turn_base__20260618-224835/dossiers \
  --dir Gemini=predictions/gemini-3.1-pro-max_3turn_base__20260919-062335/dossiers \
  --dir Grok=predictions/grok-4.6-max_3turn_base__20260919-062335/dossiers \
  --dir Astra=predictions/gpt-6-astra-max_3turn_base__20260919-082408/dossiers \
  --dir Fable=predictions/claude-fable-5-1_3turn_base__20260919-092955/dossiers
```

`vote_offline.py` scores only ids every judge in the panel has, so report the panel's N.
Also report the 5-judge panel (paper's 4 + Gemini) at N=40 for comparison with round 1.

**Per-class results and confusion matrix**, for every run in the table above:

```
mkdir -p results/per-class
python3 plot/per_class.py --run predictions/<run_dir> \
  --csv results/per-class/<judge>-mode-confusion.csv > results/per-class/<judge>.txt
```

Report per judge: how many category and failure-mode classes have only one gold example,
and the most frequent confusion pairs. Reviewers asked for exactly this, since macro-F1
over near-singleton classes is unstable.

## Task 5: update `results/revision_results.md` and push

Rewrite the results file so it stands alone. It must contain:

1. **Every judge in one table**, with N per row and 95% CIs: the paper's 4, plus Gemini,
   Grok, gpt-6-astra and Fable. Mark which runs are complete.
2. **The missing-counted-as-incorrect rows** for any run below 40/40.
3. **GPT-5.5 consistency:** the three runs, mean ± sd, run-vs-run κ with N per pair.
4. **Both voting tables** (8-judge panel with its N, and the 5-judge panel at N=40).
5. **Per-class summary** plus the paths of the confusion-matrix CSVs.
6. **The leak audit** from Task 2, including the runs that came out clean.
7. **Per-run log:** model id, request parameters, date, dossier count, missing ids and
   their errors, leak flags, empty verdicts, git SHA. Add per-run cost and token totals if
   the proxy reports them; if not, say so.
8. **Changes since round 1:** the `max_buffer_size` change, its commit hash, and which
   dossiers were produced after it.

Then commit and push `revision-judges` again, and tell the user it is ready for review,
noting anything still unresolved.

## Do not

- edit `data/`, `judge/prompts/`, or `judge/taxonomy.py`
- change prompts, models, tools or verdict parsing. The only code change in this round is
  `max_buffer_size`
- modify or delete the paper's stored runs in `predictions/` (the `20260618-*` folders)
- re-run any id more than once per round
- commit `.env` or print any key
- push to `main`
