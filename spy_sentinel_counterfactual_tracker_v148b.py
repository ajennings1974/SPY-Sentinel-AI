import json
from pathlib import Path

BASE = Path.cwd()

log = BASE / "spy_sentinel_rejections_v147b.jsonl"

if not log.exists() or not log.read_text().strip():
    print("\nV148B COUNTERFACTUAL TRACKER")
    print("No valid trackable rejection exists yet.")
    print("WAITING FOR A FRESH MARKET-HOURS REJECTION.")
    print("NO ORDER SUBMITTED")
    raise SystemExit(0)

rows = [
    json.loads(x)
    for x in log.read_text().splitlines()
    if x.strip()
]

latest = rows[-1]

print("\nV148B COUNTERFACTUAL READY")
print("Decision ID:", latest["decision_id"])
print("Symbol:", latest["symbol"])
print("Shadow entry:", latest["shadow_entry_price"])
print("Status:", latest["counterfactual_status"])
print("NO ORDER SUBMITTED")
