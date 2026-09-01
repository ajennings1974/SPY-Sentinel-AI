import json
from pathlib import Path

BASE = Path.cwd()

quality = json.loads(
    (
        BASE
        / "spy_sentinel_feature_quality_v188.json"
    ).read_text()
)

episodes = json.loads(
    (
        BASE
        / "spy_sentinel_episode_scores_v187.json"
    ).read_text()
)

ranking = []

for feature, stats in quality["features"].items():

    count = stats["count"]

    completeness = (
        stats["present"] / count
        if count
        else 0
    )

    ranking.append({
        "feature": feature,
        "completeness_score": completeness,
        "episode_support": count,
        "predictive_score": None,
        "status": (
            "INSUFFICIENT EXPERIENCE"
            if len(episodes["episodes"]) < 20
            else "READY FOR SHADOW ANALYSIS"
        )
    })


ranking.sort(
    key=lambda x: (
        x["completeness_score"],
        x["episode_support"]
    ),
    reverse=True,
)

out = BASE / "spy_sentinel_feature_ranking_v189.json"

out.write_text(
    json.dumps(
        {
            "ranking": ranking,
            "episode_count":
                len(episodes["episodes"]),
            "predictive_ranking_enabled":
                len(episodes["episodes"]) >= 20,
        },
        indent=2
    )
)

print("\nV189 CHALLENGER FEATURE RANKING")

for x in ranking:
    print(
        x["feature"],
        "| completeness:",
        round(
            x["completeness_score"] * 100,
            1
        ),
        "%",
        "|",
        x["status"]
    )

print(
    "Predictive ranking enabled:",
    len(episodes["episodes"]) >= 20
)
