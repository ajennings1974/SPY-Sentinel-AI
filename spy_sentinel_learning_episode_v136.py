import json
from pathlib import Path
from datetime import datetime

BASE = Path.cwd()

passport_file = BASE / "spy_sentinel_decision_passport_v118.json"
candidate_file = BASE / "spy_sentinel_candidate_v125.json"
experience_file = BASE / "spy_sentinel_experience_v133.json"

passport = json.loads(passport_file.read_text()) if passport_file.exists() else {}
candidate = json.loads(candidate_file.read_text()) if candidate_file.exists() else {}
experience = json.loads(experience_file.read_text()) if experience_file.exists() else {}

trade = passport.get("trade", {})
cand = candidate.get("candidate") or {}

entry_price = trade.get("entry_price")
exit_price = trade.get("exit_price")

entry_time = trade.get("entry_time")
exit_time = trade.get("exit_time")

holding_minutes = None

try:
    if entry_time and exit_time:
        t1 = datetime.fromisoformat(str(entry_time))
        t2 = datetime.fromisoformat(str(exit_time))
        holding_minutes = (t2 - t1).total_seconds() / 60
except Exception:
    pass

realized_pct = trade.get("pnl_pct")

if realized_pct is not None:
    realized_pct = float(realized_pct)

if realized_pct is not None and realized_pct <= -0.15:
    outcome_class = "LOSS_LIMIT_EVENT"
elif realized_pct is not None and realized_pct >= 0.20:
    outcome_class = "PROFIT_TARGET_EVENT"
else:
    outcome_class = trade.get("exit_reason") or "OTHER"

episode = {
    "decision_id": experience.get("decision_id"),
    "underlying": "SPY",
    "option_symbol": trade.get("symbol"),

    "market_context": {
        "spy_observed_price": candidate.get("spy_price"),
        "option_type": cand.get("type"),
        "bid": cand.get("bid"),
        "ask": cand.get("ask"),
        "spread_pct": candidate.get("spread_pct"),
        "delta": candidate.get("delta"),
        "estimated_cost": candidate.get("estimated_cost"),
    },

    "trade": {
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": trade.get("quantity"),
        "holding_minutes": holding_minutes,
        "realized_pnl_dollars": trade.get("pnl_dollars"),
        "realized_pnl_pct": realized_pct,
        "exit_reason": trade.get("exit_reason"),
    },

    "excursion": {
        "maximum_favorable_excursion_pct": None,
        "maximum_adverse_excursion_pct": None,
        "status": "NOT YET AVAILABLE — WILL BE CAPTURED LIVE ON FUTURE TRADES",
    },

    "labels": {
        "primary_outcome": outcome_class,
        "profitable": bool(realized_pct is not None and realized_pct > 0),
        "stop_loss_hit": trade.get("exit_reason") == "STOP_LOSS",
        "eligible_for_learning": True,
    },

    "model_governance": {
        "champion_changed": False,
        "challenger_allowed_to_train": True,
        "automatic_champion_promotion": False,
        "independent_validation_required": True,
    }
}

out = BASE / "spy_sentinel_learning_episode_v136.json"

out.write_text(
    json.dumps(
        episode,
        indent=2,
        default=str
    )
)

print("\nSPY SENTINEL V136 — LEARNING EPISODE")
print("Option:", episode["option_symbol"])
print("Holding minutes:", episode["trade"]["holding_minutes"])
print("Realized P/L $:", episode["trade"]["realized_pnl_dollars"])
print("Outcome class:", episode["labels"]["primary_outcome"])
print("Eligible for learning:", episode["labels"]["eligible_for_learning"])
print("Challenger may train:", episode["model_governance"]["challenger_allowed_to_train"])
print("Champion changed:", episode["model_governance"]["champion_changed"])
print("Saved:", out.name)

print("\nIMPORTANT")
print("MFE/MAE are not fabricated.")
print("Future trades will capture them continuously during monitoring.")

print("\nSAFETY")
print("PAPER ONLY")
print("LIVE TRADING DISABLED")
print("NO AUTOMATIC CHAMPION PROMOTION")
