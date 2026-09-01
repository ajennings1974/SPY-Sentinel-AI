import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

def load(name):
    p = BASE / name

    if not p.exists():
        return {}

    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

inventory = load("spy_sentinel_learning_inventory_v157.json")
challenger = load("spy_sentinel_challenger_status_v161.json")
quality = load("spy_sentinel_feature_evidence_v193.json")

report = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "clean_learning_episodes":
        inventory.get(
            "total_clean_learning_episodes",
            0
        ),

    "accepted_episodes":
        inventory.get(
            "accepted_episodes",
            0
        ),

    "clean_rejected_episodes":
        inventory.get(
            "clean_rejected_episodes",
            0
        ),

    "challenger_training_eligible":
        challenger.get(
            "training_eligible",
            False
        ),

    "feature_learning_status":
        quality.get(
            "status",
            "UNKNOWN"
        ),

    "next_priority":
        "COLLECT CLEAN MARKET-HOURS EPISODES",

    "champion_changed":
        False,

    "live_trading":
        False,
}

out = BASE / "spy_sentinel_session_learning_report_v194.json"
out.write_text(json.dumps(report, indent=2))

print("\nV194 SESSION LEARNING REPORT")

for k, v in report.items():
    print(k + ":", v)

print("Saved:", out.name)
