import json
from pathlib import Path

BASE = Path.cwd()

features = {
    "required_candidate_features": [
        "spy_price",
        "option_type",
        "bid",
        "ask",
        "spread_pct",
        "estimated_cost",
        "time_of_day",
    ],

    "required_outcome_features": [
        "entry_price",
        "exit_price",
        "holding_minutes",
        "realized_pnl_pct",
        "exit_reason",
        "mfe_pct",
        "mae_pct",
    ],

    "required_rejection_features": [
        "decision_id",
        "rejection_reasons",
        "shadow_entry_price",
        "counterfactual_return_30m",
        "counterfactual_return_60m",
        "counterfactual_return_close",
        "counterfactual_label",
    ],

    "forbidden_features": [
        "future_return_at_decision_time",
        "future_price_at_decision_time",
        "post_decision_label_as_input",
    ],

    "missing_data_policy":
        "Missing values remain missing; never fabricate.",

    "leakage_policy":
        "Only information available at decision time may train decision features.",
}

out = BASE / "spy_sentinel_feature_contract_v159.json"

out.write_text(
    json.dumps(
        features,
        indent=2
    )
)

print("\nV159 LEARNING FEATURE CONTRACT")
print("Candidate features:", len(features["required_candidate_features"]))
print("Outcome features:", len(features["required_outcome_features"]))
print("Rejected-trade features:", len(features["required_rejection_features"]))
print("Forbidden leakage features:", len(features["forbidden_features"]))
print("Saved:", out.name)
