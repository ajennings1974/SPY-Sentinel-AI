import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

BASE = Path.cwd()

def read_jsonl(name):
    p = BASE / name

    if not p.exists():
        return []

    rows = []

    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass

    return rows

registry = read_jsonl(
    "spy_sentinel_decision_registry_v149.jsonl"
)

accepted = read_jsonl(
    "spy_sentinel_experience_log_v135.jsonl"
)

rejected = read_jsonl(
    "spy_sentinel_rejections_v147b.jsonl"
)

quarantine = read_jsonl(
    "spy_sentinel_rejection_quarantine_v146b.jsonl"
)

actions = Counter(
    x.get("action")
    for x in registry
)

reasons = Counter()

for x in rejected:
    for reason in x.get("rejection_reasons", []):
        reasons[reason] += 1

summary = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "registered_trade_decisions":
        actions.get("TRADE", 0),

    "registered_no_trade_decisions":
        actions.get("NO_TRADE", 0),

    "accepted_learning_episodes":
        len(accepted),

    "rejected_learning_episodes":
        len(rejected),

    "quarantined_records":
        len(quarantine),

    "top_rejection_reasons":
        dict(reasons),

    "champion":
        "SPY_SENTINEL_CHAMPION_V1",

    "champion_changed":
        False,

    "challenger":
        "NOT YET TRAINED",

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_session_summary_v169.json"

out.write_text(
    json.dumps(
        summary,
        indent=2
    )
)

print("\nV169 SESSION SUMMARY")

for k, v in summary.items():
    print(k + ":", v)

print("Saved:", out.name)
