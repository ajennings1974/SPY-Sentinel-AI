import json
from pathlib import Path
from collections import Counter

BASE = Path.cwd()

registry = BASE / "spy_sentinel_decision_registry_v149.jsonl"
quarantine = BASE / "spy_sentinel_rejection_quarantine_v146b.jsonl"

actions = Counter()
reasons = Counter()

if registry.exists():
    for line in registry.read_text().splitlines():

        if not line.strip():
            continue

        x = json.loads(line)

        actions[x.get("action")] += 1

        for reason in x.get("reasons", []):
            reasons[reason] += 1

quarantined = 0

if quarantine.exists():
    quarantined = len([
        x for x in quarantine.read_text().splitlines()
        if x.strip()
    ])

stats = {
    "trades_taken":
        actions.get("TRADE", 0),

    "no_trade_decisions":
        actions.get("NO_TRADE", 0),

    "test_decisions":
        actions.get("TEST_ONLY", 0),

    "top_rejection_reasons":
        dict(reasons),

    "quarantined_learning_records":
        quarantined,

    "quarantined_records_train_challenger":
        False,

    "champion_changed":
        False,
}

out = BASE / "spy_sentinel_rejection_learning_stats_v156.json"

out.write_text(
    json.dumps(
        stats,
        indent=2
    )
)

print("\nV156 REJECTION LEARNING STATS")
print("Trades:", stats["trades_taken"])
print("NO TRADE decisions:", stats["no_trade_decisions"])
print("Quarantined:", quarantined)
print(
    "Quarantined records train Challenger:",
    stats["quarantined_records_train_challenger"]
)
print("Saved:", out.name)
