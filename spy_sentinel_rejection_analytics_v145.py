import json
from pathlib import Path
from collections import Counter

BASE = Path.cwd()

reject_file = BASE / "spy_sentinel_rejections_v143.jsonl"
shadow_file = BASE / "spy_sentinel_counterfactuals_v144.jsonl"
trade_file = BASE / "spy_sentinel_experience_log_v135.jsonl"

rejections = []
shadows = []
trades = []

if reject_file.exists():
    rejections = [
        json.loads(x)
        for x in reject_file.read_text().splitlines()
        if x.strip()
    ]

if shadow_file.exists():
    shadows = [
        json.loads(x)
        for x in shadow_file.read_text().splitlines()
        if x.strip()
    ]

if trade_file.exists():
    trades = [
        json.loads(x)
        for x in trade_file.read_text().splitlines()
        if x.strip()
    ]

reason_counter = Counter()

for r in rejections:
    for reason in r.get("rejection_reasons", []):
        reason_counter[reason] += 1

latest_shadow_by_id = {}

for s in shadows:
    latest_shadow_by_id[s["decision_id"]] = s

profitable_rejections = 0
losing_rejections = 0
flat_rejections = 0

for s in latest_shadow_by_id.values():

    pnl = s["hypothetical_trade"]["current_pnl_pct"]

    if pnl > 0.001:
        profitable_rejections += 1

    elif pnl < -0.001:
        losing_rejections += 1

    else:
        flat_rejections += 1

summary = {
    "trades_taken": len(trades),

    "candidates_rejected": len(rejections),

    "top_rejection_reasons": reason_counter.most_common(10),

    "counterfactual": {
        "tracked_rejections": len(latest_shadow_by_id),
        "would_currently_be_profitable": profitable_rejections,
        "would_currently_be_losing": losing_rejections,
        "approximately_flat": flat_rejections,
    }
}

out = BASE / "spy_sentinel_rejection_analytics_v145.json"

out.write_text(
    json.dumps(
        summary,
        indent=2
    )
)

print("\nSPY SENTINEL V145 — REJECTION ANALYTICS")
print("Trades taken:", summary["trades_taken"])
print("Candidates rejected:", summary["candidates_rejected"])
print("Top rejection reasons:", summary["top_rejection_reasons"])
print("Shadow tracked:", summary["counterfactual"]["tracked_rejections"])
print(
    "Rejected trades currently profitable:",
    profitable_rejections
)
print(
    "Rejected trades currently losing:",
    losing_rejections
)
print("Saved:", out.name)
