import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

trainer = json.load(
    open(
        BASE
        / "spy_sentinel_challenger_trainer_v174.json"
    )
)

report = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "champion": {
        "name":
            "SPY_SENTINEL_CHAMPION_V1",

        "status":
            "ACTIVE PAPER DECISION AUTHORITY",
    },

    "challenger": {
        "name":
            "SPY_SENTINEL_CHALLENGER_V1",

        "status":
            (
                "TRAINING ELIGIBLE"
                if trainer["training_eligible"]
                else
                "WAITING FOR CLEAN EXPERIENCE"
            ),

        "execution_permission":
            False,
    },

    "promotion_status":
        "NOT ELIGIBLE",

    "champion_changed":
        False,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_champion_challenger_report_v175.json"

out.write_text(
    json.dumps(
        report,
        indent=2
    )
)

print("\nV175 CHAMPION VS CHALLENGER")
print("Champion:", report["champion"]["name"])
print("Champion status:", report["champion"]["status"])
print("Challenger:", report["challenger"]["name"])
print("Challenger status:", report["challenger"]["status"])
print("Challenger execution:", report["challenger"]["execution_permission"])
print("Champion changed:", report["champion_changed"])
print("Live trading:", report["live_trading_enabled"])
print("Saved:", out.name)
