# Taxonomy judge

Code and stored predictions for the agent-as-a-judge evaluation in the paper.

```
judge/               the three-turn judge and its prompts
data/                the 40 worked examples with their gold labels
predictions/         the stored judge output the paper reports
appendix_examples/   source traces for five examples not on a public site
plot/                scoring and figure scripts
```

## Reproducing the tables and figure

No key or network needed. Everything is scored from `predictions/`.

```
pip install -r requirements.txt

python3 plot/score_tables.py         # per-judge agreement
python3 plot/vote_offline.py          # selective-voting ensemble
python3 plot/make_kappa_heatmap.py    # writes figures/judge-kappa-heatmap.pdf
```

Expected output:

```
Model             Cat Acc  Cat F1  Mode Acc  Mode F1
GPT-5.5              0.80    0.69      0.72     0.64
Claude-Opus-4.6      0.75    0.61      0.70     0.57
Claude-Opus-4.7      0.75    0.63      0.62     0.53
Claude-Opus-4.8      0.75    0.62      0.68     0.58

Model             Pred Acc  Pred F1  Gold Acc  Gold F1
GPT-5.5               0.72     0.64      0.72     0.62
Claude-Opus-4.6       0.70     0.57      0.80     0.70
Claude-Opus-4.7       0.62     0.53      0.70     0.58
Claude-Opus-4.8       0.68     0.58      0.78     0.69
```

```
| level    | rule | coverage      | precision      | recall         | F1    |
|----------|------|---------------|----------------|----------------|-------|
| CATEGORY | 2/4  | 40/40 (1.000) | 31/40 (0.775)  | 31/40 (0.775)  | 0.775 |
| CATEGORY | 3/4  | 35/40 (0.875) | 30/35 (0.857)  | 30/40 (0.750)  | 0.800 |
| CATEGORY | 4/4  | 28/40 (0.700) | 27/28 (0.964)  | 27/40 (0.675)  | 0.794 |
| SUBTYPE  | 2/4  | 40/40 (1.000) | 28/40 (0.700)  | 28/40 (0.700)  | 0.700 |
| SUBTYPE  | 3/4  | 35/40 (0.875) | 27/35 (0.771)  | 27/40 (0.675)  | 0.720 |
| SUBTYPE  | 4/4  | 28/40 (0.700) | 25/28 (0.893)  | 25/40 (0.625)  | 0.735 |
```

## Optionally re-running the judge

This regenerates predictions instead of scoring the stored ones. It needs model access and
a network, and writes to `judge/runs/`, which the scoring scripts do not read.

```
export JUDGE_API_KEY=...       # a key for the proxy below
export JUDGE_PROXY_HOST=...    # host serving the Anthropic /v1/messages schema

python3 judge/eval_3turn.py --model claude-opus-4-8 --reflect base
python3 judge/eval_subtype_oracle.py --model claude-opus-4-8 --reflect none
```

`--ids E1,E2` or `--limit 5` runs a subset. Re-runs are not identical to the stored
predictions: sources are fetched live and the models sample.

## Notes

Paths in the stored predictions were rewritten for anonymous review, so `/workspace/...`
was a local working directory and `anon-org` replaced a repository owner. Labels, traces
and metrics are unchanged.

`data/` and `predictions/` hold the gold labels and are blocked from the judge by
`FORBIDDEN_PATTERNS` in `judge/common.py`.

If you re-judge E6, E19, E24, E31 or E40, note that their `reference` names a relative path
such as `appendix_examples/E6/`, while the judge runs in a fresh temporary directory. Either
make that reference absolute or copy the bundle into the run directory first, or the judge
will not find the evidence.

## License

MIT, see `LICENSE`.
