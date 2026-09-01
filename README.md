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
