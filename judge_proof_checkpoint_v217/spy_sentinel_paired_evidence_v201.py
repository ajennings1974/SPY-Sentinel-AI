import os
import json
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

BASE = Path.home() / "SPY_SENTINEL_EVIDENCE_RUNTIME"
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

ET = ZoneInfo("America/New_York")
now_et = datetime.now(ET)

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

# --------------------------------------------------
# 1. FRESH SPY TRADE
# --------------------------------------------------

stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

trade_req = StockLatestTradeRequest(symbol_or_symbols="SPY")
trade_resp = stock_client.get_stock_latest_trade(trade_req)
spy_trade = trade_resp["SPY"]

spy_price = float(spy_trade.price)
spy_timestamp = spy_trade.timestamp.isoformat()

# --------------------------------------------------
# 2. DISCOVER CURRENT ACTIVE SPY PUT
# --------------------------------------------------

today = now_et.date()

params = urllib.parse.urlencode({
    "underlying_symbols": "SPY",
    "status": "active",
    "type": "put",
    "expiration_date_gte": today.isoformat(),
    "expiration_date_lte": (today + timedelta(days=7)).isoformat(),
    "limit": 10000,
})

contracts_url = (
    "https://paper-api.alpaca.markets/v2/options/contracts?"
    + params
)

contract_data = get_json(contracts_url)
contracts = contract_data.get("option_contracts", [])

usable = []

for c in contracts:
    try:
        strike = float(c["strike_price"])
        expiry = c["expiration_date"]
        symbol = c["symbol"]
    except Exception:
        continue

    if c.get("status") != "active":
        continue

    if c.get("tradable") is False:
        continue

    usable.append(
        (
            expiry,
            abs(strike - spy_price),
            strike,
            symbol,
            c
        )
    )

if not usable:
    raise RuntimeError("No active usable SPY puts found")

usable.sort(key=lambda x: (x[0], x[1]))

expiry, distance, strike, symbol, contract = usable[0]

# --------------------------------------------------
# 3. FRESH OPTION QUOTE
# --------------------------------------------------

quote_params = urllib.parse.urlencode({
    "symbols": symbol
})

quote_url = (
    "https://data.alpaca.markets/v1beta1/options/quotes/latest?"
    + quote_params
)

quote_data = get_json(quote_url)
quote = quote_data.get("quotes", {}).get(symbol)

if not quote:
    raise RuntimeError(f"No latest quote for {symbol}")

bid = quote.get("bp", quote.get("bid_price"))
ask = quote.get("ap", quote.get("ask_price"))
quote_timestamp = quote.get("t", quote.get("timestamp"))

bid = float(bid) if bid is not None else None
ask = float(ask) if ask is not None else None

mid = None
spread_pct = None

if bid is not None and ask is not None:
    mid = (bid + ask) / 2

    if mid > 0:
        spread_pct = ((ask - bid) / mid) * 100

# --------------------------------------------------
# 4. TIMESTAMP FRESHNESS
# --------------------------------------------------

quote_age_seconds = None

if quote_timestamp:
    try:
        qdt = datetime.fromisoformat(
            str(quote_timestamp).replace("Z", "+00:00")
        )
        quote_age_seconds = (
            datetime.now(timezone.utc) - qdt
        ).total_seconds()
    except Exception:
        pass

# --------------------------------------------------
# 5. WRITE IMMUTABLE PAIRED EVIDENCE
# --------------------------------------------------

record = {
    "schema": "SPY_SENTINEL_PAIRED_EVIDENCE_V201",
    "captured_at_et": now_et.isoformat(),

    "spy": {
        "symbol": "SPY",
        "price": spy_price,
        "trade_timestamp": spy_timestamp,
        "source": "ALPACA_STOCK_LATEST_TRADE",
    },

    "option": {
        "symbol": symbol,
        "expiration_date": expiry,
        "strike": strike,
        "type": "put",

        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct": spread_pct,

        "quote_timestamp": quote_timestamp,
        "quote_age_seconds": quote_age_seconds,

        "contract_status": contract.get("status"),
        "tradable": contract.get("tradable"),

        "source": "ALPACA_OPTION_LATEST_QUOTE",
    },

    "decision": "OBSERVATION_ONLY",

    "paper_order_submitted": False,
    "live_order_submitted": False,

    "learning_eligible": False,

    "integrity": {
        "fresh_spy_trade": True,
        "independent_option_quote_timestamp": bool(quote_timestamp),
        "historical_v196_modified": False,
    },
}

out = BASE / "market_evidence_v201.jsonl"

with out.open("a") as f:
    f.write(json.dumps(record, default=str) + "\n")

print("\nSPY SENTINEL V201 — PAIRED FRESH EVIDENCE")
print("Captured ET:", now_et.isoformat())

print("\nSPY")
print("Price:", spy_price)
print("Trade timestamp:", spy_timestamp)

print("\nOPTION")
print("Symbol:", symbol)
print("Expiration:", expiry)
print("Strike:", strike)
print("Bid:", bid)
print("Ask:", ask)
print("Mid:", mid)
print("Spread %:", spread_pct)
print("Quote timestamp:", quote_timestamp)
print("Quote age seconds:", quote_age_seconds)

print("\nINTEGRITY")
print("Contract active:", contract.get("status") == "active")
print("Tradable:", contract.get("tradable"))
print("Independent option timestamp:", bool(quote_timestamp))
print("Historical V196 modified: False")

print("\nSAFETY")
print("PAPER ORDER SUBMITTED: False")
print("LIVE ORDER SUBMITTED: False")
print("LEARNING ELIGIBLE: False")

print("\nSaved:", out.name)
