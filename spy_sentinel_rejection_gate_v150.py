import json
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from spy_sentinel_decision_registry_v149 import register_decision

BASE = Path.cwd()

candidate_file = BASE / "spy_sentinel_candidate_v125.json"

ET = ZoneInfo("America/New_York")

if not candidate_file.exists():
    raise RuntimeError("Candidate file missing")

data = json.loads(
    candidate_file.read_text()
)

candidate = data.get("candidate") or {}

now_et = datetime.now(ET)

minutes = (
    now_et.hour * 60
    + now_et.minute
)

market_open = (
    now_et.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

generated = datetime.fromisoformat(
    data["generated_utc"]
)

age_seconds = (
    datetime.now(timezone.utc)
    - generated.astimezone(timezone.utc)
).total_seconds()

fresh = age_seconds <= 120

symbol = candidate.get("symbol")

print("\nV150 FRESH REJECTION GATE")
print("Market open:", market_open)
print("Candidate fresh:", fresh)
print("Candidate:", symbol)

if not market_open:
    print("NO REJECTION LOGGED — MARKET CLOSED")
    raise SystemExit(0)

if not fresh:
    print("NO REJECTION LOGGED — CANDIDATE STALE")
    raise SystemExit(0)

if not symbol:
    print("NO REJECTION LOGGED — NO CANDIDATE")
    raise SystemExit(0)

record = register_decision(
    action="NO_TRADE",
    symbol=symbol,
    reasons=[
        "VALIDATION_NOT_PROVEN",
    ],
    candidate_snapshot={
        "spy_price": data.get("spy_price"),
        "bid": candidate.get("bid"),
        "ask": candidate.get("ask"),
        "mid": candidate.get("mid"),
        "spread_pct": data.get("spread_pct"),
        "delta": data.get("delta"),
    },
)

print("CLEAN REJECTION LOGGED")
print("Decision ID:", record["decision_id"])
print("NO ORDER SUBMITTED")
