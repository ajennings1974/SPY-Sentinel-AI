import json
import re
from pathlib import Path
from datetime import datetime

BASE = Path.cwd()

src = BASE / "spy_sentinel_rejection_learning_v145.jsonl"
clean = BASE / "spy_sentinel_rejection_learning_clean_v146b.jsonl"
quarantine = BASE / "spy_sentinel_rejection_quarantine_v146b.jsonl"

def option_expiry(symbol):
    if not symbol:
        return None

    m = re.match(r"^[A-Z]+(\d{6})[CP]\d+$", symbol)

    if not m:
        return None

    yy, mm, dd = (
        int(m.group(1)[0:2]),
        int(m.group(1)[2:4]),
        int(m.group(1)[4:6]),
    )

    return datetime(2000 + yy, mm, dd).date()

rows = []

if src.exists():
    for line in src.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))

clean_rows = []
bad_rows = []

for x in rows:

    reasons = []

    symbol = x.get("symbol")
    expiry = option_expiry(symbol)

    logged = None

    try:
        logged = datetime.fromisoformat(
            str(x.get("logged_utc"))
        )
    except Exception:
        reasons.append("INVALID_LOG_TIMESTAMP")

    if not x.get("decision_id"):
        reasons.append("MISSING_DECISION_ID")

    if expiry is None:
        reasons.append("INVALID_OPTION_SYMBOL")

    elif logged and logged.date() > expiry:
        reasons.append("LOGGED_AFTER_OPTION_EXPIRY")

    x["counterfactual_trackable"] = not reasons
    x["quality_issues"] = reasons
    x["eligible_for_challenger_learning"] = not reasons

    if reasons:
        bad_rows.append(x)
    else:
        clean_rows.append(x)

clean.write_text(
    "".join(json.dumps(x) + "\n" for x in clean_rows)
)

quarantine.write_text(
    "".join(json.dumps(x) + "\n" for x in bad_rows)
)

print("\nV146B REJECTION QUALITY AUDIT")
print("Total:", len(rows))
print("Clean:", len(clean_rows))
print("Quarantined:", len(bad_rows))

for x in bad_rows:
    print(
        "QUARANTINED:",
        x.get("symbol"),
        "|",
        x.get("quality_issues")
    )

print("\nNO LEARNING FROM QUARANTINED DATA")
