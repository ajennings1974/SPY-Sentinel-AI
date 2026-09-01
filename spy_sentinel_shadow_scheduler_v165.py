import json
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path.cwd()

src = BASE / "spy_sentinel_session_decisions_v163.jsonl"
out = BASE / "spy_sentinel_shadow_schedule_v165.json"

episodes = []

if src.exists():
    for line in src.read_text().splitlines():

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
            "symbol": x["symbol"],
            "shadow_entry_price": (
                x.get("candidate_snapshot", {})
                .get("mid")
            ),
            "decision_timestamp_utc":
                x["timestamp_utc"],

            "plus_30m_due_utc":
                (t + timedelta(minutes=30)).isoformat(),

            "plus_60m_due_utc":
                (t + timedelta(minutes=60)).isoformat(),

            "plus_30m_result":
                None,

            "plus_60m_result":
                None,

            "session_close_result":
                None,

            "final_label":
                None,

            "status":
                "PENDING",
        })

out.write_text(
    json.dumps(
        {"episodes": episodes},
        indent=2
    )
)

print("\nV165 SHADOW SCHEDULER")
print("Pending clean NO_TRADE episodes:", len(episodes))
print("Saved:", out.name)
