import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = Path.cwd()
ET = ZoneInfo("America/New_York")

CANDIDATE_FILE = BASE / "spy_sentinel_candidate_v125.json"
REGISTRY_FILE = BASE / "spy_sentinel_decision_registry_v149.jsonl"
SESSION_FILE = BASE / "spy_sentinel_learning_session_v166.json"
ACCEPTED_LOG = BASE / "spy_sentinel_experience_log_v135.jsonl"
REJECTED_LOG = BASE / "spy_sentinel_rejections_v147b.jsonl"

def read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def read_jsonl(path):
    if not path.exists():
        return []

    rows = []

    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass

    return rows

def candidate_key(data):
    candidate = data.get("candidate") or {}

    raw = "|".join([
        str(candidate.get("symbol")),
        str(data.get("generated_utc")),
        str(candidate.get("bid")),
        str(candidate.get("ask")),
    ])

    return hashlib.sha256(
        raw.encode()
    ).hexdigest()[:16]

candidate_data = read_json(CANDIDATE_FILE)
candidate = candidate_data.get("candidate") or {}

now = datetime.now(timezone.utc)
now_et = datetime.now(ET)

minutes = now_et.hour * 60 + now_et.minute

market_open = (
    now_et.weekday() < 5
    and 570 <= minutes < 960
)

candidate_time = None
candidate_age_seconds = None

try:
    candidate_time = datetime.fromisoformat(
        candidate_data["generated_utc"]
    ).astimezone(timezone.utc)

    candidate_age_seconds = (
        now - candidate_time
    ).total_seconds()

except Exception:
    pass

candidate_fresh = (
    candidate_age_seconds is not None
    and candidate_age_seconds <= 120
)

registry = read_jsonl(REGISTRY_FILE)
accepted = read_jsonl(ACCEPTED_LOG)
rejected = read_jsonl(REJECTED_LOG)

seen_keys = {
    x.get("candidate_key")
    for x in registry
    if x.get("candidate_key")
}

key = candidate_key(candidate_data) if candidate else None

duplicate = bool(
    key
    and key in seen_keys
)

session = {
    "generated_utc":
        now.isoformat(),

    "market_open":
        market_open,

    "candidate_present":
        bool(candidate),

    "candidate_fresh":
        candidate_fresh,

    "candidate_age_seconds":
        candidate_age_seconds,

    "candidate_key":
        key,

    "duplicate_candidate":
        duplicate,

    "accepted_episode_count":
        len(accepted),

    "rejected_episode_count":
        len(rejected),

    "learning_layer_order_submission":
        False,

    "status":
        "READY"
}

if not market_open:
    session["status"] = "MARKET_CLOSED"

elif not candidate:
    session["status"] = "NO_CANDIDATE"

elif not candidate_fresh:
    session["status"] = "STALE_CANDIDATE"

elif duplicate:
    session["status"] = "DUPLICATE_BLOCKED"

SESSION_FILE.write_text(
    json.dumps(
        session,
        indent=2,
        default=str
    )
)

print("\nV166 UNIFIED LEARNING SESSION")
print("Market open:", market_open)
print("Candidate present:", bool(candidate))
print("Candidate fresh:", candidate_fresh)
print("Candidate age seconds:", candidate_age_seconds)
print("Duplicate:", duplicate)
print("Accepted episodes:", len(accepted))
print("Rejected episodes:", len(rejected))
print("Status:", session["status"])
print("Order submission:", False)
print("Saved:", SESSION_FILE.name)
