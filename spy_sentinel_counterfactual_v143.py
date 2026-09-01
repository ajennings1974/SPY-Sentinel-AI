import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

rejection_files = sorted(
    BASE.glob("*rejection*.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

candidate_file = BASE / "spy_sentinel_candidate_v125.json"
out_file = BASE / "spy_sentinel_counterfactual_v143.json"

candidate = {}
if candidate_file.exists():
    candidate = json.loads(candidate_file.read_text())

rejection = {}
for p in rejection_files:
    try:
        x = json.loads(p.read_text())
        if isinstance(x, dict):
            rejection = x
            break
    except Exception:
        pass

c = candidate.get("candidate") or {}

snapshot_price = None

for key in ("mid", "ask", "bid"):
    try:
        if c.get(key) is not None:
            snapshot_price = float(c[key])
            break
    except Exception:
        pass

record = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "decision_id": rejection.get("decision_id"),
    "symbol": c.get("symbol"),
    "rejected": True,
    "rejection_reasons": rejection.get(
        "rejection_reasons",
        [
            "VALIDATION_NOT_PROVEN",
            "LIVE_AUTH_DISABLED"
        ]
    ),
    "shadow_entry_price": snapshot_price,
    "current_shadow_price": snapshot_price,
    "counterfactual_return_pct": None,
    "counterfactual_result": "PENDING",
    "would_have_profited": None,
    "would_have_lost": None,
    "paper_order_submitted": False,
    "live_order_submitted": False,
}

out_file.write_text(
    json.dumps(record, indent=2, default=str)
)

print("\nV143 COUNTERFACTUAL TRACKER")
print("Decision ID:", record["decision_id"])
print("Symbol:", record["symbol"])
print("Shadow entry:", record["shadow_entry_price"])
print("Result:", record["counterfactual_result"])
print("NO ORDER SUBMITTED")
print("Saved:", out_file.name)
