import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

candidate_file = BASE / "spy_sentinel_candidate_v125.json"
log_file = BASE / "spy_sentinel_rejections_v143.jsonl"

if not candidate_file.exists():
    raise RuntimeError("Candidate file not found")

x = json.loads(candidate_file.read_text())
candidate = x.get("candidate") or {}
gates = x.get("gates") or {}

if not candidate:
    raise RuntimeError("No candidate available")

paper_ready = bool(
    x.get("paper_demo_readiness", {}).get("eligible")
)

validated_ready = bool(
    x.get("validated_strategy_readiness", {}).get("eligible")
)

reasons = []

if not gates.get("candidate_exists", False):
    reasons.append("NO_CANDIDATE")

if not gates.get("liquidity_pass", False):
    reasons.append("LIQUIDITY_FAIL")

if not gates.get("atm_pass", False):
    reasons.append("ATM_FAIL")

if not gates.get("cost_pass", False):
    reasons.append("COST_FAIL")

if not gates.get("account_clear", False):
    reasons.append("ACCOUNT_NOT_CLEAR")

if not gates.get("validated_edge", False):
    reasons.append("VALIDATION_NOT_PROVEN")

if not gates.get("live_authorized", False):
    reasons.append("LIVE_AUTH_DISABLED")

decision_id = "reject-" + uuid.uuid4().hex[:12]

record = {
    "decision_id": decision_id,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),

    "underlying": "SPY",

    "candidate": {
        "symbol": candidate.get("symbol"),
        "type": candidate.get("type"),
        "bid": candidate.get("bid"),
        "ask": candidate.get("ask"),
        "mid": candidate.get("mid"),
        "spread_pct": x.get("spread_pct"),
        "delta": x.get("delta"),
        "estimated_cost": x.get("estimated_cost"),
        "spy_price": x.get("spy_price"),
    },

    "eligibility": {
        "paper_demo_eligible": paper_ready,
        "validated_strategy_eligible": validated_ready,
        "live_money_eligible": False,
    },

    "decision": (
        "VALIDATED_STRATEGY_ACCEPTED"
        if validated_ready
        else "VALIDATED_STRATEGY_REJECTED"
    ),

    "rejection_reasons": reasons,

    "primary_rejection_reason": (
        reasons[0]
        if reasons
        else None
    ),

    "shadow_tracking": {
        "enabled": not validated_ready,
        "hypothetical_entry_price": candidate.get("ask"),
        "pricing_rule": "BUY_AT_ASK_EXIT_AT_BID",
        "status": "OPEN" if not validated_ready else "NOT_REQUIRED",
    },

    "learning": {
        "eligible_for_learning": True,
        "champion_changed": False,
        "automatic_promotion": False,
    },

    "safety": {
        "order_submitted": False,
        "paper_order_submitted": False,
        "live_order_submitted": False,
    }
}

with log_file.open("a") as f:
    f.write(json.dumps(record, default=str) + "\n")

print("\nSPY SENTINEL V143 — REJECTION EPISODE")
print("Decision ID:", decision_id)
print("Candidate:", record["candidate"]["symbol"])
print("Paper-demo eligible:", paper_ready)
print("Validated eligible:", validated_ready)
print("Decision:", record["decision"])
print("Reasons:", reasons)
print("Shadow tracking:", record["shadow_tracking"]["enabled"])
print("Saved:", log_file.name)

print("\nSAFETY")
print("NO ORDER SUBMITTED")
print("LIVE TRADING DISABLED")
