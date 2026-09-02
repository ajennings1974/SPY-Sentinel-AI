import json
import hashlib
from pathlib import Path
from collections import Counter

BASE = Path.home() / "SPY_SENTINEL_EVIDENCE_RUNTIME"

def load_jsonl(name):
    p = BASE / name
    if not p.exists():
        raise RuntimeError(f"Missing required artifact: {name}")
    return [
        json.loads(x)
        for x in p.read_text().splitlines()
        if x.strip()
    ]

def sha256(name):
    p = BASE / name
    return hashlib.sha256(p.read_bytes()).hexdigest()

v196 = load_jsonl("market_evidence_v196.jsonl")
v201 = load_jsonl("market_evidence_v201.jsonl")

learning = json.loads(
    (BASE / "learning_state_v213.json").read_text()
)

episodes = learning["episodes"]
summary = learning["summary"]

paper_orders = sum(
    bool(r.get("paper_order_submitted"))
    for r in v196 + v201
)

live_orders = sum(
    bool(r.get("live_order_submitted"))
    for r in v196 + v201
)

champion_changes = sum(
    bool(e.get("champion_change_authorized"))
    for e in episodes
)

completed = [
    e for e in episodes
    if e["outcome_status"] == "LABELED_OUTCOME"
]

pending = [
    e for e in episodes
    if e["outcome_status"] == "PENDING_OUTCOME"
]

bad_old_option = sum(
    1
    for r in v196
    if (
        r.get("candidate_snapshot", {})
         .get("candidate", {})
         .get("symbol")
    )
)

checks = [
    ("V196 observations exist", len(v196) > 0),
    ("Fresh paired observations exist", len(v201) > 0),
    ("Labeled outcomes exist", len(completed) > 0),
    ("Paper orders = 0", paper_orders == 0),
    ("Live orders = 0", live_orders == 0),
    ("Champion changes = 0", champion_changes == 0),
    (
        "Independent validation required",
        summary["independent_validation_required"] is True
    ),
    (
        "Self-promotion disabled",
        summary["challenger_self_promotion_authorized"] is False
    ),
]

print("\nSPY SENTINEL — CREDENTIAL-FREE JUDGE VERIFIER V217")
print("=" * 58)

for name, passed in checks:
    print(("PASS" if passed else "FAIL"), "-", name)

print("\nCURRENT SAVED PROOF")
print("V196 observations:", len(v196))
print("Fresh paired observations:", len(v201))
print("Completed outcomes:", len(completed))
print("Pending outcomes:", len(pending))
print(
    "Training-ready outcomes:",
    summary["training_ready_outcomes"]
)
print(
    "Minimum required:",
    summary["minimum_required"]
)
print(
    "Challenger training ready:",
    summary["challenger_training_ready"]
)

print("\nSAFETY")
print("Paper orders:", paper_orders)
print("Live orders:", live_orders)
print("Champion changes:", champion_changes)
print(
    "Self-promotion authorized:",
    summary["challenger_self_promotion_authorized"]
)
print(
    "Independent validation required:",
    summary["independent_validation_required"]
)

print("\nSELF-AUDIT")
print(
    "Historical V196 records containing inherited option context:",
    bad_old_option
)
print(
    "Those records remain preserved and are not treated as clean paired evidence."
)

print("\nARTIFACT HASHES")
for name in [
    "market_evidence_v196.jsonl",
    "market_evidence_v201.jsonl",
    "learning_state_v213.json",
]:
    print(name, sha256(name))

all_pass = all(passed for _, passed in checks)

print("\nFINAL VERDICT:", "PASS" if all_pass else "FAIL")

if not all_pass:
    raise SystemExit(1)
