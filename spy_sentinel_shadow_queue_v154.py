import json
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path.cwd()

registry = BASE / "spy_sentinel_decision_registry_v149.jsonl"
out = BASE / "spy_sentinel_shadow_queue_v154.json"

queue = []

if registry.exists():
    for line in registry.read_text().splitlines():

        if not line.strip():
            continue

        x = json.loads(line)

        if x.get("action") != "NO_TRADE":
            continue

        t = datetime.fromisoformat(
            x["timestamp_utc"]
        )

        queue.append({
            "decision_id": x["decision_id"],
            "symbol": x.get("symbol"),
            "decision_timestamp_utc": x["timestamp_utc"],
            "shadow_entry_price": (
                x.get("candidate_snapshot", {})
                .get("mid")
            ),
            "checkpoints": {
                "plus_30m": {
                    "due_utc":
                        (t + timedelta(minutes=30)).isoformat(),
                    "price": None,
                    "return_pct": None,
                    "classification": None,
                },
                "plus_60m": {
                    "due_utc":
                        (t + timedelta(minutes=60)).isoformat(),
                    "price": None,
                    "return_pct": None,
                    "classification": None,
                },
                "session_close": {
                    "price": None,
                    "return_pct": None,
                    "classification": None,
                },
            },
            "status": "PENDING",
            "champion_changed": False,
        })

out.write_text(
    json.dumps(
        {"episodes": queue},
        indent=2
    )
)

print("\nV154 SHADOW QUEUE")
print("Pending shadow episodes:", len(queue))
print("Saved:", out.name)
print("NO ORDER SUBMITTED")
