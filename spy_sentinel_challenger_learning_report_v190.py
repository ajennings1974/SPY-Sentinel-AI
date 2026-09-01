import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

scores = json.loads(
    (
        BASE
        / "spy_sentinel_episode_scores_v187.json"
    ).read_text()
)

ranking = json.loads(
    (
        BASE
        / "spy_sentinel_feature_ranking_v189.json"
    ).read_text()
)

report = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "clean_episode_count":
        scores["count"],

    "predictive_feature_ranking_enabled":
        ranking["predictive_ranking_enabled"],

    "challenger_training_status":
        (
            "WAITING FOR CLEAN EXPERIENCE"
            if not ranking["predictive_ranking_enabled"]
            else "READY FOR SHADOW FEATURE ANALYSIS"
        ),

    "champion":
        "SPY_SENTINEL_CHAMPION_V1",

    "champion_changed":
        False,

    "challenger_execution_authority":
        False,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_challenger_learning_report_v190.json"

out.write_text(
    json.dumps(
        report,
        indent=2
    )
)

print("\nV190 CHALLENGER LEARNING REPORT")

for k, v in report.items():
    print(k + ":", v)

print("Saved:", out.name)
