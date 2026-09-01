import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

evidence_file = BASE / "spy_sentinel_market_evidence_v181.json"
registry_file = BASE / "spy_sentinel_clean_decisions_v182.jsonl"

if not evidence_file.exists():
    raise RuntimeError("Market evidence file missing")

e = json.loads(evidence_file.read_text())

if not e["eligible_as_clean_market_evidence"]:
    print("\nV182 DECISION LOGGER")
    print("NO DECISION LOGGED")
    print("Reason: evidence is not clean/current market evidence")
    print("NO ORDER SUBMITTED")
    raise SystemExit(0)

paper = e.get("paper_readiness") or {}
validated = e.get("validated_readiness") or {}

paper_ready = bool(
    paper.get("eligible")
)

validated_ready = bool(
    validated.get("eligible")
)

action = (
    "PAPER_READY"
    if paper_ready
    else "NO_TRADE"
)

reasons = []

if not paper_ready:
    reasons.append(
        "PAPER_GATES_NOT_PASSED"
    )

if not validated_ready:
    reasons.append(
        "VALIDATION_NOT_PROVEN"
    )

decision_id = (
    "decision-"
    + uuid.uuid4().hex[:12]
)

record = {
    "decision_id": decision_id,
    "timestamp_utc":
        datetime.now(timezone.utc).isoformat(),
    "action": action,
    "symbol": e["symbol"],
    "reasons": reasons,
    "market_snapshot": {
        "spy_price": e["spy_price"],
        "bid": e["bid"],
        "ask": e["ask"],
        "mid": e["mid"],
        "spread_pct": e["spread_pct"],
        "delta": e["delta"],
        "estimated_cost": e["estimated_cost"],
    },
    "paper_order_submitted": False,
    "live_order_submitted": False,
    "eligible_for_learning": True,
    "champion_changed": False,
}

with registry_file.open("a") as f:
    f.write(
        json.dumps(
            record,
            default=str
        )
        + "\n"
    )

print("\nV182 CLEAN DECISION")
print("Decision ID:", decision_id)
print("Action:", action)
print("Symbol:", e["symbol"])
print("Reasons:", reasons)
print("Saved:", registry_file.name)
print("NO ORDER SUBMITTED")
