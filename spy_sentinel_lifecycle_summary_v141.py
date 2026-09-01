import json
from pathlib import Path
from collections import Counter

BASE = Path.cwd()

event_file = BASE / "spy_sentinel_monitor_events_v140.jsonl"
state_file = BASE / "spy_sentinel_monitor_state_v140.json"

events = []

if event_file.exists():
    for line in event_file.read_text().splitlines():
        if line.strip():
            try:
                events.append(
                    json.loads(line)
                )
            except Exception:
                pass

event_types = Counter(
    e.get("event")
    for e in events
)

summary = {
    "event_count": len(events),
    "event_types": dict(event_types),
    "unique_decision_ids": sorted(
        set(
            e.get("decision_id")
            for e in events
            if e.get("decision_id")
        )
    ),
    "state_present": state_file.exists(),
    "paper_only": True,
    "live_trading_enabled": False,
    "exit_submission_enabled": False,
}

out = BASE / "spy_sentinel_lifecycle_summary_v141.json"

out.write_text(
    json.dumps(
        summary,
        indent=2
    )
)

print("\nSPY SENTINEL V141 — LIFECYCLE SUMMARY")
print("Events:", summary["event_count"])
print("Decision IDs:", len(summary["unique_decision_ids"]))
print("State present:", summary["state_present"])
print("Exit submission enabled:", summary["exit_submission_enabled"])
print("Saved:", out.name)
