import os
import json
import urllib.parse
import urllib.request
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

BASE = Path.home() / "SPY_SENTINEL_EVIDENCE_RUNTIME"
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

ET = ZoneInfo("America/New_York")
now = datetime.now(ET)

source = BASE / "market_evidence_v201.jsonl"
out = BASE / "learning_state_v213.json"

rows = [
    json.loads(x)
    for x in source.read_text().splitlines()
    if x.strip()
]

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

episodes = []

for r in rows:
    captured = datetime.fromisoformat(r["captured_at_et"])
    age_minutes = (now - captured).total_seconds() / 60

    option = r["option"]
    symbol = option["symbol"]

    stable_id = hashlib.sha256(
        (r["captured_at_et"] + "|" + symbol).encode()
    ).hexdigest()[:12]

    episode = {
        "episode_id": "V213-" + stable_id,
        "captured_at_et": r["captured_at_et"],
        "spy_entry": r["spy"]["price"],
        "option_symbol": symbol,
        "option_entry_mid": option["mid"],
        "age_minutes": age_minutes,
        "paper_order_submitted": False,
        "live_order_submitted": False,
        "champion_change_authorized": False,
    }

    if age_minutes < 20:
        episode.update({
            "outcome_status": "PENDING_OUTCOME",
            "outcome_label": None,
            "hypothetical_return_pct": None,
            "challenger_training_eligible": False,
            "reason": "20_MINUTE_MEASUREMENT_HORIZON_NOT_REACHED",
        })

        episodes.append(episode)
        continue

    params = urllib.parse.urlencode({"symbols": symbol})

    url = (
        "https://data.alpaca.markets/v1beta1/options/quotes/latest?"
        + params
    )

    data = get_json(url)
    q = data.get("quotes", {}).get(symbol)

    if not q:
        episode.update({
            "outcome_status": "UNRESOLVED",
            "outcome_label": None,
            "hypothetical_return_pct": None,
            "challenger_training_eligible": False,
            "reason": "LATEST_OPTION_QUOTE_UNAVAILABLE",
        })

        episodes.append(episode)
        continue

    bid = q.get("bp", q.get("bid_price"))
    ask = q.get("ap", q.get("ask_price"))
    quote_ts = q.get("t", q.get("timestamp"))

    bid = float(bid) if bid is not None else None
    ask = float(ask) if ask is not None else None

    if bid is None or ask is None:
        current_mid = None
    else:
        current_mid = (bid + ask) / 2

    entry_mid = float(option["mid"])

    if current_mid is None or entry_mid == 0:
        ret = None
        label = "UNRESOLVED"
    else:
        ret = ((current_mid - entry_mid) / entry_mid) * 100

        if ret > 1:
            label = "HYPOTHETICALLY_PROFITABLE"
        elif ret < -1:
            label = "HYPOTHETICALLY_LOSING"
        else:
            label = "HYPOTHETICALLY_FLAT"

    measured = label != "UNRESOLVED"

    episode.update({
        "outcome_status": (
            "LABELED_OUTCOME"
            if measured
            else "UNRESOLVED"
        ),
        "outcome_label": label,
        "current_option_bid": bid,
        "current_option_ask": ask,
        "current_option_mid": current_mid,
        "current_quote_timestamp": quote_ts,
        "hypothetical_return_pct": ret,
        "actual_trade_occurred": False,
        "challenger_training_eligible": measured,
        "reason": (
            "MEASURED_COUNTERFACTUAL_OUTCOME"
            if measured
            else "OUTCOME_COULD_NOT_BE_RESOLVED"
        ),
    })

    episodes.append(episode)

completed = [
    x for x in episodes
    if x["outcome_status"] == "LABELED_OUTCOME"
]

training = [
    x for x in completed
    if x["challenger_training_eligible"]
]

MINIMUM = 10

state = {
    "schema": "SPY_SENTINEL_LEARNING_PIPELINE_V213",
    "evaluated_at_et": now.isoformat(),
    "source_records": len(rows),
    "episodes": episodes,
    "summary": {
        "pending": sum(
            x["outcome_status"] == "PENDING_OUTCOME"
            for x in episodes
        ),
        "completed": len(completed),
        "training_ready_outcomes": len(training),
        "minimum_required": MINIMUM,
        "challenger_training_ready": (
            len(training) >= MINIMUM
        ),
        "independent_validation_required": True,
        "challenger_execution_authorized": False,
        "challenger_self_promotion_authorized": False,
        "champion_change_authorized": False,
        "paper_orders": 0,
        "live_orders": 0,
    },
}

out.write_text(json.dumps(state, indent=2, default=str))

print("\nSPY SENTINEL V213 — AUTOMATIC LEARNING PIPELINE")
print("Source paired records:", len(rows))
print("Pending:", state["summary"]["pending"])
print("Completed:", state["summary"]["completed"])
print(
    "Training-ready:",
    state["summary"]["training_ready_outcomes"]
)
print("Minimum required:", MINIMUM)
print(
    "Challenger ready:",
    state["summary"]["challenger_training_ready"]
)
print("Champion change authorized: False")
print("Paper orders: 0")
print("Live orders: 0")
print("Saved:", out.name)
