import json
from pathlib import Path

BASE = Path.cwd()

schema = {
    "required_identity": [
        "decision_id",
        "decision_timestamp_utc",
        "action",
        "symbol",
    ],

    "decision_time_features": [
        "spy_price",
        "option_type",
        "bid",
        "ask",
        "mid",
        "spread_pct",
        "estimated_cost",
        "time_of_day",
    ],

    "accepted_trade_outcome": [
        "entry_price",
        "exit_price",
        "holding_minutes",
        "realized_pnl_pct",
        "exit_reason",
        "mfe_pct",
        "mae_pct",
    ],

    "rejected_trade_outcome": [
        "counterfactual_return_30m",
        "counterfactual_return_60m",
        "counterfactual_return_close",
        "counterfactual_label",
    ],

    "governance": {
        "future_information_allowed_as_input": False,
        "quarantined_data_allowed": False,
        "missing_values_fabricated": False,
        "champion_changed_automatically": False,
    }
}

out = BASE / "spy_sentinel_evidence_schema_v190.json"
out.write_text(json.dumps(schema, indent=2))

print("\nV190 EVIDENCE SCHEMA")
print("Decision-time features:", len(schema["decision_time_features"]))
print("Future leakage allowed:", schema["governance"]["future_information_allowed_as_input"])
print("Missing values fabricated:", schema["governance"]["missing_values_fabricated"])
print("Saved:", out.name)
