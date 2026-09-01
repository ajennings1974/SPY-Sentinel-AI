import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

decision_id = "spy-" + uuid.uuid4().hex[:12]

passport_file = BASE / "spy_sentinel_decision_passport_v118.json"
experience_file = BASE / "spy_sentinel_experience_v133.json"

passport = {}
experience = {}

if passport_file.exists():
    passport = json.loads(passport_file.read_text())

if experience_file.exists():
    experience = json.loads(experience_file.read_text())

trade = passport.get("trade", {})

episode = {
    "decision_id": decision_id,
    "created_utc": datetime.now(timezone.utc).isoformat(),

    "instrument": {
        "underlying": "SPY",
        "option_symbol": trade.get("symbol"),
    },

    "decision": {
        "environment": "ALPACA PAPER",
        "live_trading_enabled": False,
        "research_edge_proven": False,
        "execution_mode": "CONTROLLED PAPER DEMO",
    },

    "entry": {
        "price": trade.get("entry_price"),
        "time": trade.get("entry_time"),
        "quantity": trade.get("quantity"),
    },

    "exit": {
        "price": trade.get("exit_price"),
        "time": trade.get("exit_time"),
        "reason": trade.get("exit_reason"),
    },

    "outcome": {
        "realized_pnl_dollars": trade.get("pnl_dollars"),
        "realized_pnl_pct": trade.get("pnl_pct"),
        "label": experience.get("outcome_label", "STOP_LOSS"),
        "eligible_for_learning": True,
    },

    "learning": {
        "champion_changed": False,
        "automatic_retraining": False,
        "promotion_required": True,
        "promotion_path": [
            "Experience Log",
            "Outcome Labels",
            "Challenger Model",
            "Independent Validation",
            "Champion Promotion",
        ],
    },

    "audit": {
        "decision_passport_present": passport_file.exists(),
        "experience_record_present": experience_file.exists(),
    },
}

log_path = BASE / "spy_sentinel_experience_log_v135.jsonl"

with log_path.open("a") as f:
    f.write(json.dumps(episode, default=str) + "\n")

print("\nSPY SENTINEL V135 — EXPERIENCE LOG")
print("Decision ID:", decision_id)
print("Option:", episode["instrument"]["option_symbol"])
print("Exit reason:", episode["exit"]["reason"])
print("P/L $:", episode["outcome"]["realized_pnl_dollars"])
print("Learning eligible:", episode["outcome"]["eligible_for_learning"])
print("Champion changed:", episode["learning"]["champion_changed"])
print("Saved:", log_path.name)

print("\nSAFETY")
print("PAPER ONLY")
print("LIVE TRADING DISABLED")
print("NO AUTOMATIC MODEL PROMOTION")
