import json
from pathlib import Path

BASE = Path.cwd()

requirements = {
    "rolling_oos_pass":
        False,

    "fresh_paper_pass":
        False,

    "positive_expectancy_after_costs":
        False,

    "drawdown_not_worse":
        False,

    "abstention_quality_not_worse":
        False,

    "reproducible":
        False,

    "no_leakage":
        False,
}

passed = sum(requirements.values())
total = len(requirements)

result = {
    "promotion_gates":
        requirements,

    "passed":
        passed,

    "total":
        total,

    "promotion_ready":
        passed == total,

    "champion_changed":
        False,
}

out = BASE / "spy_sentinel_promotion_score_v180.json"

out.write_text(
    json.dumps(result, indent=2)
)

print("\nV180 PROMOTION SCORE")
print("Passed:", passed, "/", total)
print("Promotion ready:", result["promotion_ready"])
print("Champion changed:", result["champion_changed"])
