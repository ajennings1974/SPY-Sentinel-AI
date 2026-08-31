import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

BASE = Path.cwd()
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

# Reuse the real contract selected by our working agent.
audit_file = BASE / "spy_sentinel_agent_v96_audit.json"

if not audit_file.exists():
    raise RuntimeError("V96 audit file not found")

audit = json.loads(
    audit_file.read_text()
)

candidate = audit.get("candidate")

if not candidate:
    raise RuntimeError("No candidate found in V96 audit")

symbol = candidate["symbol"]

print("\nV103 HISTORICAL OPTIONS PROBE")
print("Option symbol:", symbol)

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

end = datetime.now(timezone.utc) - timedelta(minutes=20)
start = end - timedelta(days=10)

url = (
    "https://data.alpaca.markets"
    "/v1beta1/options/bars"
)

params = {
    "symbols": symbol,
    "timeframe": "5Min",
    "start": start.isoformat(),
    "end": end.isoformat(),
    "limit": 10000,
    "sort": "asc",
}

r = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30,
)

print("HTTP status:", r.status_code)

if r.status_code != 200:
    print("Response:", r.text[:800])
    raise SystemExit(1)

payload = r.json()

bars = payload.get("bars", {})

if isinstance(bars, dict):
    option_bars = bars.get(symbol, [])
else:
    option_bars = []

print("Historical bars returned:", len(option_bars))

if option_bars:
    print("First bar:", option_bars[0])
    print("Last bar:", option_bars[-1])

print(
    "Next page token:",
    bool(payload.get("next_page_token"))
)

print("\nV103 RESULT")
print(
    "Historical options backfill available:"
    ,
    len(option_bars) > 0
)

print("\nSAFETY")
print("HISTORICAL DATA ONLY")
print("NO ORDER CODE")
print("PAPER/LIVE EXECUTION UNCHANGED")
