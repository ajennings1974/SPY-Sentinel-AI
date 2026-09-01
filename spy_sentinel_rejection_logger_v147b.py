import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = Path.cwd()

candidate_file = BASE / "spy_sentinel_candidate_v125.json"
out = BASE / "spy_sentinel_rejections_v147b.jsonl"

ET = ZoneInfo("America/New_York")

def expiry_from_symbol(symbol):
    if not symbol:
        return None

    m = re.match(r"^[A-Z]+(\d{6})[CP]\d+$", symbol)

    if not m:
        return None

    y = 2000 + int(m.group(1)[0:2])
    mth = int(m.group(1)[2:4])
    d = int(m.group(1)[4:6])

    return datetime(y, mth, d).date()

if not candidate_file.exists():
    raise RuntimeError("Candidate file missing")

c = json.loads(candidate_file.read_text())

candidate = c.get("candidate") or {}
symbol = candidate.get("symbol")

generated = datetime.fromisoformat(
    c["generated_utc"]
)

now = datetime.now(timezone.utc)

age_seconds = (
    now - generated.astimezone(timezone.utc)
).total_seconds()

expiry = expiry_from_symbol(symbol)

today_et = datetime.now(ET).date()

issues = []

if not symbol:
    issues.append("NO_CANDIDATE")

if expiry is None:
    issues.append("INVALID_EXPIRY")

elif expiry < today_et:
    issues.append("OPTION_EXPIRED")

if age_seconds > 120:
    issues.append("STALE_CANDIDATE")

trackable = not issues

if not trackable:
    print("\nV147B REJECTION LOGGER")
    print("REJECTION NOT LOGGED")
    print("Reasons:", issues)
    print("No learning episode created.")
    raise SystemExit(0)

decision_id = "reject-" + uuid.uuid4().hex[:12]

record = {
    "decision_id": decision_id,
    "decision_timestamp_utc": now.isoformat(),
    "candidate_snapshot_timestamp_utc": c["generated_utc"],
    "symbol": symbol,
    "expiry": str(expiry),
    "shadow_entry_price": candidate.get("mid"),
    "bid": candidate.get("bid"),
    "ask": candidate.get("ask"),
    "spread_pct": c.get("spread_pct"),
    "rejection_reasons": [
        "VALIDATION_NOT_PROVEN",
        "LIVE_AUTH_DISABLED",
    ],
    "counterfactual_trackable": True,
    "counterfactual_status": "PENDING",
    "champion_changed": False,
}

with out.open("a") as f:
    f.write(json.dumps(record) + "\n")

print("\nV147B FRESH REJECTION LOGGED")
print("Decision ID:", decision_id)
print("Symbol:", symbol)
print("Expiry:", expiry)
print("Candidate age seconds:", round(age_seconds, 1))
print("Counterfactual trackable: True")
print("NO ORDER SUBMITTED")
