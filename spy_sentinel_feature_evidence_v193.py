import json
from pathlib import Path
from collections import defaultdict

BASE = Path.cwd()

episode_files = [
    BASE / "spy_sentinel_learning_episode_v136.json",
]

scores = defaultdict(list)

for p in episode_files:
    if not p.exists():
        continue

    try:
        x = json.loads(p.read_text())
    except Exception:
        continue

    context = x.get("market_context", {})
    labels = x.get("labels", {})

    profitable = labels.get("profitable")

    quality = 1.0 if profitable else 0.0

    for key in [
        "spy_observed_price",
        "spread_pct",
        "estimated_cost",
    ]:
        value = context.get(key)

        if value is not None:
            scores[key].append({
                "value": value,
                "decision_quality": quality,
            })

result = {
    "feature_observations": dict(scores),
    "episode_count": sum(
        len(v)
        for v in scores.values()
    ),
    "status": "INSUFFICIENT SAMPLE — DESCRIPTIVE ONLY",
    "champion_changed": False,
}

out = BASE / "spy_sentinel_feature_evidence_v193.json"
out.write_text(json.dumps(result, indent=2, default=str))

print("\nV193 FEATURE EVIDENCE")
print("Features observed:", list(scores.keys()))
print("Observations:", result["episode_count"])
print("Status:", result["status"])
print("Champion changed:", result["champion_changed"])
