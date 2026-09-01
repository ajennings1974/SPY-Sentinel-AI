import json
from pathlib import Path

BASE = Path.cwd()

schema = {
    "schema_version": "1.0",

    "required_identity": [
        "decision_id",
        "timestamp_utc",
        "action",
        "symbol",
    ],

    "candidate_features": [
        "spy_price",
        "bid",
        "ask",
        "mid",
        "spread_pct",
        "delta",
        "estimated_cost",
    ],

    "decision_features": [
        "action",
        "reasons",
        "paper_eligible",
        "validated_strategy_eligible",
        "live_money_eligible",
    ],

    "accepted_outcome_features": [
        "entry_price",
        "exit_price",
        "holding_minutes",
        "mfe_pct",
        "mae_pct",
        "realized_pnl_pct",
        "exit_reason",
    ],

    "rejected_outcome_features": [
        "shadow_entry_price",
        "return_30m",
        "return_60m",
        "return_close",
        "counterfactual_label",
    ],

    "allowed_actions": [
        "TRADE",
        "NO_TRADE",
    ],

    "allowed_counterfactual_labels": [
        "GOOD_ABSTENTION",
        "MISSED_OPPORTUNITY",
        "NEUTRAL",
        "PENDING",
    ],

    "quarantine_if_missing": [
        "decision_id",
        "timestamp_utc",
        "symbol",
    ],

    "future_data_as_decision_input":
        False,

    "fabricated_missing_values":
        False,
}

out = BASE / "spy_sentinel_learning_schema_v167.json"

out.write_text(
    json.dumps(
        schema,
        indent=2
    )
)

print("\nV167 LEARNING SCHEMA")
print("Schema version:", schema["schema_version"])
print("Allowed actions:", schema["allowed_actions"])
print("Future data allowed as input:", schema["future_data_as_decision_input"])
print("Fabricated values:", schema["fabricated_missing_values"])
print("Saved:", out.name)
