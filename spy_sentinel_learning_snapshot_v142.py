import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

governance_file = BASE / "spy_sentinel_governance_v137.json"
dataset_file = BASE / "spy_sentinel_learning_dataset_v138.json"
lifecycle_file = BASE / "spy_sentinel_lifecycle_summary_v141.json"

governance = (
    json.loads(governance_file.read_text())
    if governance_file.exists()
    else {}
)

dataset = (
    json.loads(dataset_file.read_text())
    if dataset_file.exists()
    else {}
)

lifecycle = (
    json.loads(lifecycle_file.read_text())
    if lifecycle_file.exists()
    else {}
)

snapshot = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "champion":
        governance.get(
            "architecture",
            {}
        ).get(
            "champion",
            "UNKNOWN"
        ),

    "challenger":
        governance.get(
            "architecture",
            {}
        ).get(
            "challenger",
            "NOT YET TRAINED"
        ),

    "experience_episodes":
        governance.get(
            "current_learning_state",
            {}
        ).get(
            "experience_episodes",
            0
        ),

    "learning_episodes":
        dataset.get(
            "learning_episode_count",
            0
        ),

    "lifecycle_events":
        lifecycle.get(
            "event_count",
            0
        ),

    "champion_changed":
        governance.get(
            "champion_changed",
            False
        ),

    "automatic_promotion":
        False,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_learning_snapshot_v142.json"

out.write_text(
    json.dumps(
        snapshot,
        indent=2
    )
)

print("\nSPY SENTINEL V142 — LEARNING SNAPSHOT")
print("Champion:", snapshot["champion"])
print("Challenger:", snapshot["challenger"])
print("Experience episodes:", snapshot["experience_episodes"])
print("Learning episodes:", snapshot["learning_episodes"])
print("Lifecycle events:", snapshot["lifecycle_events"])
print("Champion changed:", snapshot["champion_changed"])
print("Automatic promotion:", snapshot["automatic_promotion"])
print("Live trading:", snapshot["live_trading_enabled"])
print("Saved:", out.name)
