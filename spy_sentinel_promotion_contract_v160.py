import json
from pathlib import Path

BASE = Path.cwd()

contract = {
    "challenger_may_train_when":
        "V158 evidence gate passes",

    "challenger_may_not_trade":
        True,

    "promotion_requirements": {
        "rolling_out_of_sample_pass":
            True,

        "fresh_paper_validation_pass":
            True,

        "positive_expectancy_after_costs":
            True,

        "max_drawdown_not_worse_than_champion":
            True,

        "reproducible_results":
            True,

        "no_data_leakage":
            True,

        "minimum_sample_size_met":
            True,
    },

    "promotion_authority":
        "Governance gate only",

    "automatic_self_promotion":
        False,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_promotion_contract_v160.json"

out.write_text(
    json.dumps(
        contract,
        indent=2
    )
)

print("\nV160 PROMOTION CONTRACT")

for k, v in contract["promotion_requirements"].items():
    print(k + ":", v)

print(
    "Automatic self-promotion:",
    contract["automatic_self_promotion"]
)

print(
    "Live trading:",
    contract["live_trading_enabled"]
)

print("Saved:", out.name)
