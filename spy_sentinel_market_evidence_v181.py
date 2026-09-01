import json
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = Path.cwd()

candidate_file = BASE / "spy_sentinel_candidate_v125.json"
out_file = BASE / "spy_sentinel_market_evidence_v181.json"

ET = ZoneInfo("America/New_York")

if not candidate_file.exists():
    raise RuntimeError("Candidate file missing")

data = json.loads(candidate_file.read_text())

candidate = data.get("candidate") or {}

generated = datetime.fromisoformat(
    data["generated_utc"]
)

now_utc = datetime.now(timezone.utc)
now_et = datetime.now(ET)

age_seconds = (
    now_utc
    - generated.astimezone(timezone.utc)
).total_seconds()

minutes = now_et.hour * 60 + now_et.minute

market_open = (
    now_et.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

fresh = age_seconds <= 120

record = {
    "generated_utc": now_utc.isoformat(),
    "market_open": market_open,
    "candidate_fresh": fresh,
    "candidate_age_seconds": age_seconds,
    "spy_price": data.get("spy_price"),
    "symbol": candidate.get("symbol"),
    "type": candidate.get("type"),
    "bid": candidate.get("bid"),
    "ask": candidate.get("ask"),
    "mid": candidate.get("mid"),
    "spread_pct": data.get("spread_pct"),
    "delta": data.get("delta"),
    "estimated_cost": data.get("estimated_cost"),
    "paper_readiness": data.get("paper_demo_readiness"),
    "validated_readiness": data.get("validated_strategy_readiness"),
    "eligible_as_clean_market_evidence": (
        market_open
        and fresh
        and bool(candidate.get("symbol"))
    ),
    "paper_order_submitted": False,
    "live_order_submitted": False,
}

out_file.write_text(
    json.dumps(
        record,
        indent=2,
        default=str
    )
)

print("\nV181 MARKET EVIDENCE")
print("Market open:", market_open)
print("Candidate fresh:", fresh)
print("Candidate age seconds:", round(age_seconds, 1))
print("Symbol:", record["symbol"])
print(
    "Eligible as clean evidence:",
    record["eligible_as_clean_market_evidence"]
)
print("Saved:", out_file.name)

print("\nNO ORDER SUBMITTED")
