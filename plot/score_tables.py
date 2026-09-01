import json
import warnings
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).parent.parent

BASE = {
    "GPT-5.5": "gpt-5.5-xhigh_3turn_base__20260618-160352",
    "Claude-Opus-4.6": "claude-opus-4-6_3turn_base__20260618-160352",
    "Claude-Opus-4.7": "claude-opus-4-7_3turn_base__20260618-160352",
    "Claude-Opus-4.8": "opus-4.8_3turn_base__20260618-224835",
}
ORACLE = {
    "GPT-5.5": "gpt-5.5-xhigh_3turn-oracle_none__20260618-142516",
    "Claude-Opus-4.6": "claude-opus-4-6_3turn-oracle_none__20260618-161410",
    "Claude-Opus-4.7": "claude-opus-4-7_3turn-oracle_none__20260618-173357",
    "Claude-Opus-4.8": "opus-4.8_3turn-oracle_none__20260618-152627",
}


def score(run):
    yc, pc, ys, ps = [], [], [], []
    for f in (ROOT / "predictions" / run / "dossiers").glob("*.json"):
        d = json.loads(f.read_text())
        g, p = d["gold"], d["pred"]
        yc.append(f"{g['edge']}|{g['fault_side']}")
        pc.append(f"{p['edge']}|{p['fault_side']}")
        ys.append(f"{g['edge']}|{g['fault_side']}|{g['failure_mode']}")
        ps.append(f"{p['edge']}|{p['fault_side']}|{p['failure_mode']}")
    macro = lambda a, b: f1_score(a, b, average="macro", zero_division=0)
    return accuracy_score(yc, pc), macro(yc, pc), accuracy_score(ys, ps), macro(ys, ps)


print("Table 2 — each judge vs human labels")
print(f"{'Model':16}{'Cat Acc':>9}{'Cat F1':>8}{'Mode Acc':>10}{'Mode F1':>9}")
for name, run in BASE.items():
    ca, cf, ma, mf = score(run)
    print(f"{name:16}{ca:9.2f}{cf:8.2f}{ma:10.2f}{mf:9.2f}")

print("\nTable 3 — failure-mode agreement (4 strongest judges)")
print(f"{'Model':16}{'Pred Acc':>10}{'Pred F1':>9}{'Gold Acc':>10}{'Gold F1':>9}")
for name in ("GPT-5.5", "Claude-Opus-4.6", "Claude-Opus-4.7", "Claude-Opus-4.8"):
    _, _, pa, pf = score(BASE[name])
    _, _, ga, gf = score(ORACLE[name])
    print(f"{name:16}{pa:10.2f}{pf:9.2f}{ga:10.2f}{gf:9.2f}")
