# CLAUDE.md: judge runs for the ARR revision

This repo holds the judge code and stored results for the paper "Model or Harness?"
(arXiv 2607.28802). Reviewers asked for (1) judges from more model families and
(2) evidence that a judge labels consistently across repeated runs. Your job is to run
those experiments and report the results. The paper's protocol must not change. If
anything in these instructions can't be followed, stop and ask the user; don't work
around it.

**Round 2:** if `results/revision_results.md` already exists, the first round is done;
follow `CLAUDE-2.md` instead, which lists the remaining work and refers back here for
setup and protocol.

Read `README.md` and `REPRODUCE.md` first. In short: `judge/eval_3turn.py` runs an
agentic judge (Claude Agent SDK, routed through a LiteLLM proxy) on the 40 examples in
`data/examples.jsonl`, and writes one timestamped folder per run under `judge/runs/`.

## Tasks

1. **Four new judges**, one full run each:
   - the latest Grok model
   - the latest Gemini model
   - `gpt-6-astra`
   - Claude Fable 5.1 (`claude-fable-5-1`)
2. **Consistency:** run GPT-5.5 (`gpt-5.5-xhigh`, the paper's strongest judge) **2 more
   times** with the exact paper config. With the stored run, that makes 3.
3. **Score** everything with confidence intervals and write `results/revision_results.md`.

## Setup

```
pip install -r requirements.txt
```

`.env` must exist in the repo root with `JUDGE_API_KEY`, `JUDGE_PROXY_HOST` (host only,
no `https://`), `DOCENT_API_KEY` and `GH_TOKEN`. If it is missing or incomplete, stop
and ask the user for the values. Never print the keys, and never commit `.env`.

The code reads the keys from `.env`, but it reads `JUDGE_PROXY_HOST` only from the shell
environment; without it, requests go to a placeholder host. Before running anything, load
`.env` into the shell and run every script from the repo root:

```
set -a; . ./.env; set +a
```

**Check model access before any run.** Send a 1-token request for every model id you
plan to use (see "Resolve model ids") **and for `claude-sonnet-4-6`**. The judge calls
`claude-sonnet-4-6` to repair malformed JSON verdicts, so the key must allow it too.

```
curl -s -X POST "https://$JUDGE_PROXY_HOST/v1/messages" -H "content-type: application/json" \
  -H "Authorization: Bearer $JUDGE_API_KEY" \
  -d '{"model":"<model-id>","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'
```

A 403, or a message like "this key may only call ...", means the key doesn't cover that
model. Report the exact error for each blocked model. If `claude-sonnet-4-6` or
`gpt-5.5` is blocked, stop and ask the user for a key that covers them.

The Agent SDK normally bundles the `claude` CLI. If it reports the CLI is missing, run
`npm install -g @anthropic-ai/claude-code`.

Five examples (E6, E19, E24, E31, E40) reference local files in `appendix_examples/`,
but the judge runs in a temp dir. Copy the bundles outside the repo and export their
location (`judge/dataset.py` rewrites the references):

```
mkdir -p /tmp/taxjudge-bundles && cp -r appendix_examples/* /tmp/taxjudge-bundles/
export TAXJUDGE_BUNDLES=/tmp/taxjudge-bundles
```

That path must not contain `predictions`, `examples.jsonl` or `agent-failure-taxonomy`,
which match the answer-key block list in `judge/common.py`.

## Resolve model ids

List what the proxy serves:

```
curl -s -H "Authorization: Bearer $JUDGE_API_KEY" "https://$JUDGE_PROXY_HOST/v1/models" | python3 -m json.tool | grep '"id"'
```

- **Grok / Gemini:** pick the newest Grok and Gemini model ids in that list. Prefer the
  full flagship model over mini/flash/lite variants. If the listing endpoint fails (some
  proxies return 404/405), don't guess ids: stop and ask the user for the exact Grok and
  Gemini ids.
- **`gpt-6-astra` and `claude-fable-5-1`:** confirm they appear under those ids (or a
  close variant).

If any of the four is missing, report which one and continue with the rest; don't
substitute another model.

**Reasoning settings.** The paper ran GPT-5.5 at maximum reasoning effort (`xhigh`, see
`ALIASES` in `judge/common.py`). Match that where the model supports it:
- **Non-Claude models** (Grok, Gemini, gpt-6-astra): add an `ALIASES` entry that sets the
  highest supported reasoning effort, following the `gpt-5.5-xhigh` pattern, and pass that
  alias as `--model`.
- **Claude models** (`claude-fable-5-1`): no alias needed. `judge_3turn.py` drops `ALIASES`
  extras for any model id starting with `claude`, which is how the paper ran the Opus judges.

Record the exact model id and parameters used for each run.

## Smoke test (each new model)

```
python3 judge/eval_3turn.py --model <model-or-alias> --reflect base --ids E1,E24
```

Pass criteria for the new folder in `judge/runs/`:
- both dossiers exist
- `pred.category` is non-empty
- `leaks` is `[]`
- E24's `trajectory` shows the judge reading `/tmp/taxjudge-bundles/E24`

If a model can't use tools through the proxy, record the error and skip that model. Do
not edit prompts or judge logic to make it work.

## Full runs

Always pass `--reflect base`: it is the paper's setup (dossier → classify → reflect).
Runs are long agentic sessions, so start them in the background with a log:

```
mkdir -p logs results
nohup python3 judge/eval_3turn.py --model <model-or-alias> --reflect base > logs/<name>.log 2>&1 &
```

- One run per new model (4 runs).
- `--model gpt-5.5-xhigh --reflect base`, run twice as two separate runs.
- **Run at most 2 full runs at a time**, not all 6 at once. Each run holds
  `TAXJUDGE_CONCURRENCY` (default 3) judge sessions open, and too many at once can exhaust
  the key's rate or budget limit. Lower the concurrency if the proxy returns rate-limit errors.
- **Watch the logs while runs are going.** If most examples in a run error, or you see a 403
  that mentions a budget or limit, stop all runs and report the exact error to the user. Don't
  start retries: they will fail the same way.

## Checks after each run

For each run folder in `judge/runs/`:
- **40 dossiers.** For errored or missing ids, re-run just those (`--ids E7,E12`) and copy
  the new dossiers into the original run's `dossiers/`. Then move the retry run's folder
  into the original run's `retries/` subfolder so each model has one run folder. Retry each
  id **at most once**. If more than 5 ids error in one run, or the retry fails with the same
  error, stop retrying. Report the ids and the error to the user, since it usually means a
  key or proxy problem that more retries won't fix.
- `manifest.json` is not updated when you copy in dossiers from a retry. Ignore it: the
  dossiers are the source of truth, and the scoring scripts read only those.
- **`leaks` is `[]` in every dossier.** A non-empty `leaks` means the judge touched the
  answer key: delete that dossier and re-run the id.
  - Exception: E31's own bundled transcript mentions `agent-failure-taxonomy`, so a tool
    call that searches that transcript can be flagged even though no answer key was read.
    If E31 is flagged twice, stop re-running it and list the flagged tool calls in the
    results file.
- **Empty `pred.category`.** Count the dossiers with an unparseable verdict and report
  them; don't fix them by hand.

Then copy each finished run folder into `predictions/`. Scoring reads only from there.

**Score complete runs (40/40) as the headline numbers.** The scoring scripts silently
score whatever dossiers exist, so a partial run gives numbers over a smaller set without
warning. For any run that can't reach 40 after one retry, still report it, but:
- state N in every row (e.g. "Grok 4.6, N=39"), and
- add a second row that counts each missing example as incorrect, so nobody can read the
  score as the result of dropping hard examples.

List each run's missing ids and their errors. Group runs under one name in
`bootstrap_ci.py` only when they use the same model id and parameters.

**Per-class results and confusion matrix** (reviewers asked for both), for every complete
run:

```
python3 plot/per_class.py --run predictions/<run_dir> --csv results/<judge>-mode-confusion.csv
```

It prints per-class precision/recall/F1 with support at the category and failure-mode
level, flags classes with a single gold example, lists the most frequent confusions, and
writes the full failure-mode confusion matrix as CSV.

## Deliverable: `results/revision_results.md`

- the `bootstrap_ci.py` table for all judges, with CIs
- GPT-5.5 consistency: the 3 runs, mean ± sd, and run-vs-run κ
- the voting table for all 8 judges
- per run: model id and parameters, date, number of errors/leaks/empty verdicts, git SHA
- per-class tables and the confusion-matrix CSVs from `plot/per_class.py`, including how
  many classes have only one gold example
- any model that was skipped, and why

## Do not

- edit `data/`, `judge/prompts/`, or `judge/taxonomy.py`
- modify or delete anything already in `predictions/`
- commit `.env` or print any key
- push to `main`. Commit to a branch named `revision-judges` and **push that branch**
  (`git push -u origin revision-judges`), including the new run folders under
  `predictions/`, so others can rescore them. Then tell the user it is ready for review.
