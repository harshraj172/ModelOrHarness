# CLAUDE-2.md: round 2 of the ARR revision runs

Round 1 produced six new judge runs and `results/revision_results.md` on branch
`revision-judges`. This file is the work that remains. `CLAUDE.md` still holds the setup
(`.env`, `set -a; . ./.env; set +a`, bundles, model access check) and the protocol rules
(paper config `--reflect base`, one retry per id, at most 2 runs at a time, never edit
`data/`, `judge/prompts/`, `judge/taxonomy.py`). Read it first, then do the tasks below
**in order**. If anything can't be followed, stop and ask the user.

Round 1 left five gaps: the runs were never shared, four runs are incomplete, judge-vs-judge
agreement was never computed, per-class results and the confusion matrix are missing, and
the blocked answer-key attempts were never audited. Tasks 1–7 close all five.

Terminology: "the four new runs" = Gemini, Grok, gpt-6-astra, Fable. Four runs are
incomplete: those three new judges plus the GPT-5.5 repeat run 2.

## Task 1: commit and push what already exists

Round 1 may have left files uncommitted. Commit first, then push:

```
git checkout revision-judges
git status --short                      # inspect before adding
git add predictions results && git commit -m "round 1: new judge runs and results"
git push -u origin revision-judges
```

`predictions/` is **not** gitignored, so no `-f` is needed; `judge/runs/` and `logs/` are
ignored on purpose, so don't force-add them. Verify the runs actually reached the remote:

```
git ls-tree -r --name-only origin/revision-judges | grep -c '^predictions/'
```

That count must cover every dossier of all six runs. If the push fails for
authentication, stop and ask the user; don't put a token in a command or a remote URL.

## Task 2: finish the incomplete runs

Every missing dossier comes from one harness limit: `claude_agent_sdk` aborts a session
with `CLIJSONDecodeError: Failed to decode JSON: JSON message exceeded maximum buffer size
of 1048576 bytes` when one CLI message exceeds 1 MiB. `ClaudeAgentOptions` accepts
`max_buffer_size` (verified in SDK 0.2.152+), so raise it.

1. In `judge/judge_3turn.py`, in the `ClaudeAgentOptions(...)` call inside `label()` (the
   only such call in the package), add:

   ```python
   max_buffer_size=64 * 1024 * 1024,
   ```

2. Commit that alone, e.g. "harness: raise SDK stdout buffer to 64 MiB (no change to
   prompts or judge logic)". Record the commit hash for the results file. This is
   transport plumbing: it changes no model, prompt, tool or verdict parsing.
3. Re-run only these (run, id) pairs, each with its own model/alias and `--reflect base`:

   | run folder | model / alias | ids |
   |---|---|---|
   | `grok-4.6-max_3turn_base__20260919-062335` | `grok-4.6-max` | E14 |
   | `gpt-6-astra-max_3turn_base__20260919-082408` | `gpt-6-astra-max` | E10, E16, E32 |
   | `claude-fable-5-1_3turn_base__20260919-092955` | `claude-fable-5-1` | E16 |
   | `gpt-5.5-xhigh_3turn_base__20260919-105038` (run 2) | `gpt-5.5-xhigh` | E25 |

   Six pairs in total.
4. Copy each new dossier into that run's `dossiers/` in **both** `judge/runs/` and
   `predictions/`, and move the re-run's folder under the run's `retries/`. Before copying,
   check the dossier's internal `"id"` matches its filename, so a dossier can never be
   filed under the wrong example or the wrong run. Don't regenerate `manifest.json`.
5. One attempt per id. If the buffer change doesn't fix an id, report the new error and
   stop; don't try a third time.
6. Leave the 4 empty verdicts in the gpt-6-astra run (E2, E3, E29, E38) as they are. They
   score as incorrect. Report them (Task 6).
7. Also copy each run's `manifest.json` and `run.log` from `judge/runs/<run>/` next to its
   `dossiers/` in `predictions/`, so the model id, parameters and git SHA travel with the
   run.

## Task 3: audit answer-key access (after Task 2, so re-runs are covered)

```
python3 plot/leak_audit.py                 # every run in predictions/
python3 plot/leak_audit.py --verbose       # with each flagged step
```

The script pairs every suspicious tool call with its result and classifies it as WEB QUERY
(a web search that only mentions the taxonomy: harmless), DENIED (the hook refused it),
UNDECIDABLE (the result is missing or was truncated when recorded), or READ (gold-shaped
content came back). It reports E31 separately, because E31's own bundled transcript
mentions the taxonomy; that is expected and is not evidence of a leak.

- A run is clean only if it has **no READ and no UNDECIDABLE**. On the paper's stored runs
  the script reports 0 of both, which is the baseline to compare against.
- For any READ: that dossier is invalid. Delete it, re-run the id once, and say so in the
  results file.
- For any UNDECIDABLE: inspect the dossier by hand and state the conclusion. Do not
  re-run E31 on the basis of its expected hits.
- Report the result for **every** run, including the paper's four, and including runs that
  come out clean. The clean result is the evidence that the reported κ values are not
  contaminated.

## Task 4: judge-vs-judge agreement (reviewer asked for this)

A reviewer argued that agreement among four judges may reflect shared model priors, since
three were Claude. With judges from four families, that is now testable.

`plot/make_kappa_heatmap.py` computes pairwise Cohen's κ among the judges and the human
labels, but its `DIRS` lists only the paper's four runs. Add the four new runs to `DIRS`
(name → `<run>/dossiers` path), then:

```
python3 plot/make_kappa_heatmap.py
```

Report, from the resulting matrix:
- the full pairwise κ matrix (judges and human),
- mean κ **within** the Claude family (Opus 4.6/4.7/4.8, Fable) vs **across** families
  (e.g. Gemini vs GPT-5.5, Gemini vs Opus, Grok vs Opus),
- each judge's κ with the human labels, for comparison.

If within-family κ is not markedly higher than across-family κ, say so plainly: that is
the answer to the shared-priors objection.

## Task 5: rescore everything

Offline from `predictions/`. Run the sanity check first; it must reproduce the paper
(GPT-5.5 category κ = 0.76):

```
python3 plot/bootstrap_ci.py
```

Then all eight judges. A wrong path now fails loudly rather than printing `N=0`, but check
that every row shows the N you expect:

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

**Any run still below 40/40:** run the same command again with `--missing-wrong` and report
both rows. Compare those rows on **accuracy and κ only**; the script prints why macro-F1
is not comparable there (the sentinel adds a class).

**GPT-5.5 consistency** (three runs; repeating the name groups them and prints mean ± sd
plus run-vs-run agreement at both category and failure-mode level):

```
python3 plot/bootstrap_ci.py \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260618-160352 \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260919-105038 \
  --run GPT-5.5=predictions/gpt-5.5-xhigh_3turn_base__20260919-105615 
```

State N for each pair: mean ± sd mixes runs of different N unless all three reach 40/40
after Task 2.

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

Two caveats to report, not to hide:
- `vote_offline.py` scores only ids that **every** panel member has, so state the panel's N.
- It drops a judge's empty verdict from the tally, so on the gpt-6-astra empty ids (E2, E3,
  E29, E38) the panel is effectively 7, not 8. List those ids and say what the vote would be
  if those ids were excluded entirely.

Also report the 5-judge panel (paper's 4 + Gemini) at N=40, for comparison with round 1.

**Per-class results and confusion matrix**, for each of the 8 runs named in the
`bootstrap_ci.py` command above, using the same short names:

```
mkdir -p results/per-class
python3 plot/per_class.py --run predictions/<run_dir> \
  --csv results/per-class/<ShortName>-mode-confusion.csv > results/per-class/<ShortName>.txt
```

Report per judge: the number of category and failure-mode classes with only one gold
example, the size of the label set (gold ∪ predicted, since macro-F1 averages over it, so
a judge that invents more classes is averaged over more), and the most frequent confusion
pairs.

## Task 6: rewrite `results/revision_results.md`

It must stand alone and contain:

1. **One table with every judge**, N per row and 95% CIs: the paper's 4 plus the 4 new
   ones; mark which runs are complete.
2. **Missing-counted-as-incorrect rows** for any run below 40/40, compared on accuracy and κ.
3. **GPT-5.5 consistency:** three runs, mean ± sd, run-vs-run agreement and κ at category
   and failure-mode level, with N per pair.
4. **Judge-vs-judge κ** from Task 4: the matrix, within-family vs across-family means, and
   what that says about shared priors.
5. **Both voting tables** (8-judge with its N and the empty-verdict caveat; 5-judge at N=40).
6. **Per-class summary** and the paths of the confusion-matrix CSVs.
7. **The leak audit** from Task 3 for every run, clean ones included.
8. **Per-run log:** model id, request parameters, date, dossier count, missing ids with
   their errors, leak verdicts, empty verdicts, git SHA (from the copied `manifest.json`).
   Add cost and token totals only if the proxy reports them; the judge code records none,
   so otherwise write "not recorded".
9. **Changes since round 1:** the `max_buffer_size` commit hash, which dossiers were
   produced after it, and any dossier deleted and re-run because of the audit.

## Task 7: publish

```
git add -A && git commit -m "round 2: complete runs, audits, per-class results"
git push
gh pr create --base main --head revision-judges \
  --title "Revision judge runs: 4 new families, consistency, per-class results" \
  --body-file results/revision_results.md
```

A pushed branch notifies nobody, so open the PR. If `gh` isn't authenticated, say so and
give the user the branch name instead. Then tell the user it is ready for review, listing
anything still unresolved.

## Do not

- edit `data/`, `judge/prompts/`, or `judge/taxonomy.py`
- change prompts, models, tools or verdict parsing; the only code changes this round are
  `max_buffer_size` and adding entries to `DIRS` in `plot/make_kappa_heatmap.py`
- modify or delete the paper's stored runs (`predictions/*20260618-*`)
- re-run any id more than once per round, or re-run an id because you dislike its label
- commit `.env` or print any key
- push to `main` directly
