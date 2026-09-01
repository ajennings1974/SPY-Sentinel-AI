import json
from pathlib import Path
from collections import defaultdict

BASE = Path.cwd()

data = json.loads(
    (
        BASE
        / "spy_sentinel_episode_scores_v187.json"
    ).read_text()
)

feature_stats = defaultdict(
    lambda: {
        "count": 0,
        "present": 0,
        "missing": 0,
    }
)

for episode in data["episodes"]:

    features = episode.get("features", {})

    for name, value in features.items():

        feature_stats[name]["count"] += 1

        if value is None:
            feature_stats[name]["missing"] += 1
        else:
            feature_stats[name]["present"] += 1


result = {
    "features": dict(feature_stats),
    "episode_count": len(data["episodes"]),
}

out = BASE / "spy_sentinel_feature_quality_v188.json"

out.write_text(
    json.dumps(
        result,
        indent=2
    )
)

print("\nV188 FEATURE QUALITY")

for name, stats in sorted(
    result["features"].items()
):
    print(
        name,
        "| present:",
        stats["present"],
        "| missing:",
        stats["missing"]
    )

print("Saved:", out.name)
