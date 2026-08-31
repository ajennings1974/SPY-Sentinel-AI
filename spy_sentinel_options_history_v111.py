import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

BASE = Path.cwd()
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

print("\nV111 60-DAY LEAKAGE-SAFE OPTIONS DATASET")
print("Goal: test multiple historical near-ATM SPY contracts")

# ----------------------------------------
# 1. GET RECENT HISTORICAL SPY BARS
# ----------------------------------------

stock = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY
)

end = datetime(2026, 8, 15, tzinfo=timezone.utc)
start = end - timedelta(days=120)

req = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(
        1,
        TimeFrameUnit.Day
    ),
    start=start,
    end=end,
)

spy = stock.get_stock_bars(req).df.reset_index()

if "symbol" in spy.columns:
    spy = spy[spy["symbol"] == "SPY"]

spy["timestamp"] = pd.to_datetime(
    spy["timestamp"],
    utc=True
)

print("SPY trading days:", len(spy))

# Use only the last 20 complete trading days before Aug 17
spy = spy.tail(61).copy()

# IMPORTANT:
# Contract strikes for each trading day are chosen
# from the PREVIOUS trading day's close only.
spy["selection_price"] = spy["close"].shift(1)

spy = spy.dropna(
    subset=["selection_price"]
).copy()

# ----------------------------------------
# 2. OCC SYMBOL BUILDER
# ----------------------------------------

def occ_symbol(expiry, cp, strike):
    # SPY + YYMMDD + C/P + strike*1000 padded to 8 digits
    strike_code = f"{int(round(strike * 1000)):08d}"

    return (
        "SPY"
        + expiry.strftime("%y%m%d")
        + cp
        + strike_code
    )

# ----------------------------------------
# 3. TEST NEAR-ATM CALLS + PUTS
# ----------------------------------------

results = []

bars_url = (
    "https://data.alpaca.markets"
    "/v1beta1/options/bars"
)

for _, row in spy.iterrows():

    trade_date = row["timestamp"].date()
    spy_close = float(row["close"])

    # LEAKAGE-SAFE:
    # today's contract universe is selected using
    # yesterday's already-known SPY close.
    selection_price = float(
        row["selection_price"]
    )

    atm = round(selection_price)

    # Pilot expirations:
    # try next 1-5 calendar days
    expiry_candidates = [
        trade_date + timedelta(days=d)
        for d in range(1, 6)
    ]

    symbols = []

    for expiry in expiry_candidates:

        for strike in [
            atm - 2,
            atm - 1,
            atm,
            atm + 1,
            atm + 2,
        ]:

            symbols.append(
                occ_symbol(
                    expiry,
                    "C",
                    strike
                )
            )

            symbols.append(
                occ_symbol(
                    expiry,
                    "P",
                    strike
                )
            )

    query_start = datetime.combine(
        trade_date,
        datetime.min.time(),
        tzinfo=timezone.utc
    )

    query_end = query_start + timedelta(days=1)

    r = requests.get(
        bars_url,
        headers=headers,
        params={
            "symbols": ",".join(symbols),
            "timeframe": "5Min",
            "start": query_start.isoformat(),
            "end": query_end.isoformat(),
            "limit": 10000,
            "sort": "asc",
        },
        timeout=30,
    )

    print(
        "\nDate:",
        trade_date,
        "| SPY:",
        round(spy_close, 2),
        "| HTTP:",
        r.status_code,
    )

    if r.status_code != 200:
        print(
            "Response:",
            r.text[:300]
        )
        continue

    payload = r.json()

    bars = payload.get(
        "bars",
        {}
    )

    contracts_with_data = 0
    total_bars = 0

    if isinstance(bars, dict):

        for symbol, rows in bars.items():

            if not rows:
                continue

            contracts_with_data += 1
            total_bars += len(rows)

            for b in rows:

                results.append({
                    "trade_date":
                        trade_date,
                    "spy_close":
                        spy_close,
                    "option_symbol":
                        symbol,
                    "timestamp":
                        b.get("t"),
                    "open":
                        b.get("o"),
                    "high":
                        b.get("h"),
                    "low":
                        b.get("l"),
                    "close":
                        b.get("c"),
                    "volume":
                        b.get("v"),
                    "trade_count":
                        b.get("n"),
                    "vwap":
                        b.get("vw"),
                })

    print(
        "Contracts with data:",
        contracts_with_data
    )

    print(
        "Option bars:",
        total_bars
    )

# ----------------------------------------
# 4. SAVE PILOT
# ----------------------------------------

out = pd.DataFrame(results)

out_file = (
    BASE
    / "spy_sentinel_options_history_v111.csv"
)

out.to_csv(
    out_file,
    index=False
)

print("\nV111 60-DAY DATASET RESULT")
print("Rows saved:", len(out))

if not out.empty:

    print(
        "Unique contracts:",
        out["option_symbol"].nunique()
    )

    print(
        "Trading dates:",
        out["trade_date"].nunique()
    )

print(
    "Saved:",
    out_file.name
)

print("\nSAFETY")
print("HISTORICAL DATA ONLY")
print("NO ORDER CODE")
print("PAPER/LIVE EXECUTION UNCHANGED")
