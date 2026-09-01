import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from spy_sentinel_session_decision_v163 import create_decision

BASE = Path.cwd()
PYTHON = BASE.parent / ".venv" / "bin" / "python"

ET = ZoneInfo("America/New_York")
now = datetime.now(ET)

minutes = now.hour * 60 + now.minute

market_open = (
    now.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

full_learning_window = (
    now.weekday() < 5
    and minutes >= 570
    and minutes <= 900
)

print("\nV164 MARKET LEARNING SESSION")
print("Eastern time:", now.isoformat())
print("Market open:", market_open)
print("Full learning window:", full_learning_window)

if not market_open:
    print("FAIL CLOSED: MARKET CLOSED")
    print("NO DECISION EPISODE CREATED")
    raise SystemExit(0)

if not full_learning_window:
    print("FAIL CLOSED: INSUFFICIENT TIME FOR +60M SHADOW CHECK")
    print("NO NEW LEARNING EPISODE CREATED")
    raise SystemExit(0)

# Refresh candidate first.
r = subprocess.run(
    [str(PYTHON), str(BASE / "spy_sentinel_candidate_v125.py")],
    cwd=str(BASE),
)

if r.returncode != 0:
    raise RuntimeError("Candidate refresh failed")

candidate_file = BASE / "spy_sentinel_candidate_v125.json"

if not candidate_file.exists():
    raise RuntimeError("Candidate JSON missing")

data = json.loads(candidate_file.read_text())
candidate = data.get("candidate") or {}

symbol = candidate.get("symbol")

if not symbol:
    print("NO VALID CANDIDATE")
    raise SystemExit(0)

# We remain conservative:
# current research validation is not proven.
action = "NO_TRADE"

reasons = [
    "VALIDATION_NOT_PROVEN"
]

snapshot = {
    "spy_price": data.get("spy_price"),
    "option_symbol": symbol,
    "option_type": candidate.get("type"),
    "bid": candidate.get("bid"),
    "ask": candidate.get("ask"),
    "mid": candidate.get("mid"),
    "spread_pct": data.get("spread_pct"),
    "delta": data.get("delta"),
    "estimated_cost": data.get("estimated_cost"),
    "paper_readiness": data.get("paper_demo_readiness"),
    "validated_readiness": data.get("validated_strategy_readiness"),
}

x = create_decision(
    action=action,
    symbol=symbol,
    candidate_snapshot=snapshot,
    reasons=reasons,
)

print("\nDECISION CREATED")
print("Decision ID:", x["decision_id"])
print("Action:", action)
print("Symbol:", symbol)
print("Reasons:", reasons)
print("Counterfactual required:", x["counterfactual_required"])
print("NO ORDER SUBMITTED")
