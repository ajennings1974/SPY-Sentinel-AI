import json
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path.cwd()

registry = BASE / "spy_sentinel_decision_registry_v149.jsonl"
out = BASE / "spy_sentinel_shadow_schedule_v151.json"

episodes = []

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

        episodes.append({
            "decision_id": x["decision_id"],
            "symbol": x.get("symbol"),
            "decision_timestamp_utc": x["timestamp_utc"],
            "checkpoints": {
                "plus_30m": (t + timedelta(minutes=30)).isoformat(),
                "plus_60m": (t + timedelta(minutes=60)).isoformat(),
                "session_close": "16:00 America/New_York",
            },
            "status": "PENDING",
        })

out.write_text(
    json.dumps(
        {
            "shadow_episodes": episodes
        },
        indent=2
    )
)

print("\nV151 SHADOW SCHEDULE")
print("Trackable rejections:", len(episodes))
print("Saved:", out.name)
