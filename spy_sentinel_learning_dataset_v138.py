import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

log_file = BASE / "spy_sentinel_experience_log_v135.jsonl"
enriched_file = BASE / "spy_sentinel_learning_episode_v136.json"

raw_episodes = []

if log_file.exists():
    for line in log_file.read_text().splitlines():
        if not line.strip():
            continue

        try:
            raw_episodes.append(json.loads(line))
        except Exception:
            pass

enriched = {}

if enriched_file.exists():
    enriched = json.loads(
        enriched_file.read_text()
    )

dataset = {
    "generated_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "dataset_name":
        "SPY_SENTINEL_EXPERIENCE_DATASET",

    "raw_episode_count":
        len(raw_episodes),

    "learning_episode_count":
        1 if enriched else 0,

    "episodes": [],

    "governance": {
        "used_for_champion_directly":
            False,

        "challenger_training_allowed":
            True,

        "champion_promotion_allowed":
            False,

        "independent_validation_required":
            True,
    },
}

if enriched:

    enriched = dict(enriched)

    if not enriched.get("decision_id"):
        enriched["decision_id"] = (
            "legacy-first-completed-paper-trade"
        )

    dataset["episodes"].append(
        enriched
    )

out = (
    BASE
    / "spy_sentinel_learning_dataset_v138.json"
)

out.write_text(
    json.dumps(
        dataset,
        indent=2,
        default=str
    )
)

print("\nSPY SENTINEL V138 — LEARNING DATASET")
print(
    "Raw experience episodes:",
    dataset["raw_episode_count"]
)
print(
    "Enriched learning episodes:",
    dataset["learning_episode_count"]
)

if dataset["episodes"]:
    e = dataset["episodes"][0]

    print(
        "First decision ID:",
        e.get("decision_id")
    )

    print(
        "Outcome:",
        e.get(
            "labels",
            {}
        ).get(
            "primary_outcome"
        )
    )

print(
    "Used directly by Champion:",
    dataset["governance"]["used_for_champion_directly"]
)

print(
    "Independent validation required:",
    dataset["governance"]["independent_validation_required"]
)

print("Saved:", out.name)
