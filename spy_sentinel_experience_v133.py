import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

passport_file = (
    BASE
    / "decision_passports"
    / "first_complete_paper_trade.json"
)

if not passport_file.exists():
    raise RuntimeError(
        "First completed trade passport not found"
    )

passport = json.loads(
    passport_file.read_text()
)

trade = passport.get("trade", {})

decision_id = (
    "SPY-"
    + datetime.now(
        timezone.utc
    ).strftime("%Y%m%d")
    + "-"
    + uuid.uuid4().hex[:8]
)

entry_price = trade.get("entry_price")
exit_price = trade.get("exit_price")

holding_minutes = None

try:
    entry_time = datetime.fromisoformat(
        trade["entry_time"]
    )
    exit_time = datetime.fromisoformat(
        trade["exit_time"]
    )

    holding_minutes = (
        exit_time - entry_time
    ).total_seconds() / 60

except Exception:
    pass

experience = {
    "decision_id": decision_id,

    "created_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "system":
        "SPY Sentinel AI",

    "environment":
        "ALPACA PAPER",

    "episode_type":
        "COMPLETED_TRADE",

    "candidate": {
        "symbol":
            trade.get("symbol"),

        "quantity":
            trade.get("quantity"),
    },

    "entry": {
        "option_price":
            entry_price,

        "timestamp":
            trade.get("entry_time"),

        "spy_price":
            None,

        "bid":
            None,

        "ask":
            None,

        "spread_pct":
            None,
    },

    "exit": {
        "option_price":
            exit_price,

        "timestamp":
            trade.get("exit_time"),

        "spy_price":
            None,

        "reason":
            trade.get("exit_reason"),
    },

    "outcome": {
        "realized_pnl_dollars":
            trade.get("pnl_dollars"),

        "realized_pnl_pct":
            trade.get("pnl_pct"),

        "holding_minutes":
            holding_minutes,

        "maximum_favorable_excursion_pct":
            None,

        "maximum_adverse_excursion_pct":
            None,

        "initial_label":
            trade.get("exit_reason"),
    },

    "governance": {
        "research_edge_proven":
            False,

        "paper_only":
            True,

        "live_trading_enabled":
            False,

        "champion_model_changed":
            False,
    },

    "learning_status": {
        "eligible_for_learning":
            True,

        "reviewed":
            False,

        "challenger_used":
            False,

        "promotion_effect":
            "NONE",
    },
}

log_file = (
    BASE
    / "spy_sentinel_experience_log_v133.jsonl"
)

with log_file.open("a") as f:
    f.write(
        json.dumps(
            experience,
            default=str
        )
        + "\n"
    )

print("\nV133 EXPERIENCE LOG")
print("Decision ID:", decision_id)
print("Episode: COMPLETED_TRADE")
print(
    "P/L $:",
    experience["outcome"][
        "realized_pnl_dollars"
    ]
)
print(
    "P/L %:",
    experience["outcome"][
        "realized_pnl_pct"
    ]
)
print(
    "Holding minutes:",
    holding_minutes
)
print(
    "Outcome label:",
    experience["outcome"][
        "initial_label"
    ]
)

print("\nLEARNING")
print("Eligible for learning: True")
print("Champion changed: False")
print("Automatic retraining: DISABLED")

print("\nSAFETY")
print("PAPER ONLY")
print("LIVE TRADING: DISABLED")
