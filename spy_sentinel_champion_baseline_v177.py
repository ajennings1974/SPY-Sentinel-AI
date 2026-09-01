import json
from pathlib import Path

BASE = Path.cwd()

baseline = {
    "champion_id":
        "SPY_SENTINEL_CHAMPION_V1",

    "decision_authority":
        "ACTIVE PAPER DECISION AUTHORITY",

    "baseline_metrics_required": [
        "trade_count",
        "win_rate",
        "average_return",
        "expectancy",
        "max_drawdown",
        "profit_factor",
        "good_abstention_rate",
        "missed_opportunity_rate",
    ],

    "promotion_rule":
        "Challenger must beat Champion on risk-adjusted out-of-sample performance.",

    "champion_may_not_self_modify":
        True,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_champion_baseline_v177.json"

out.write_text(
    json.dumps(baseline, indent=2)
)

print("\nV177 CHAMPION BASELINE")
print("Champion:", baseline["champion_id"])
print("Required metrics:", len(baseline["baseline_metrics_required"]))
print("Self modification:", False)
print("Live trading:", False)
