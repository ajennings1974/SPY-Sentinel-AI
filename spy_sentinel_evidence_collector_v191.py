import json
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = Path.cwd()
ET = ZoneInfo("America/New_York")

candidate_file = BASE / "spy_sentinel_candidate_v125.json"
registry_file = BASE / "spy_sentinel_decision_registry_v149.jsonl"
out_file = BASE / "spy_sentinel_clean_evidence_v191.jsonl"

now_et = datetime.now(ET)
minutes = now_et.hour * 60 + now_et.minute

market_open = (
    now_et.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

print("\nV191 CLEAN EVIDENCE COLLECTOR")
print("Market open:", market_open)

if not market_open:
    print("FAIL CLOSED — MARKET CLOSED")
    print("NO EVIDENCE EPISODE CREATED")
    raise SystemExit(0)

if not candidate_file.exists():
    raise RuntimeError("Candidate snapshot missing")

c = json.loads(candidate_file.read_text())

generated = datetime.fromisoformat(c["generated_utc"])
age = (
    datetime.now(timezone.utc)
    - generated.astimezone(timezone.utc)
).total_seconds()

if age > 120:
    print("FAIL CLOSED — CANDIDATE STALE")
    raise SystemExit(0)

candidate = c.get("candidate") or {}

record = {
    "decision_id": None,
    "decision_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "action": "PENDING_DECISION",
    "symbol": candidate.get("symbol"),
    "features": {
        "spy_price": c.get("spy_price"),
        "option_type": candidate.get("type"),
        "bid": candidate.get("bid"),
        "ask": candidate.get("ask"),
        "mid": candidate.get("mid"),
        "spread_pct": c.get("spread_pct"),
        "estimated_cost": c.get("estimated_cost"),
        "time_of_day": now_et.strftime("%H:%M"),
    },
    "outcome_status": "PENDING",
    "eligible_for_learning": False,
    "champion_changed": False,
}

with out_file.open("a") as f:
    f.write(json.dumps(record, default=str) + "\n")

print("Clean candidate evidence captured")
print("Symbol:", record["symbol"])
print("Learning eligible:", record["eligible_for_learning"])
print("NO ORDER SUBMITTED")
