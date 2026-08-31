import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# ------------------------------------------
# PATHS
# ------------------------------------------

BASE = Path.cwd()

env_file = BASE / ".env"
load_dotenv(env_file)

telemetry_file = BASE / "spy_sentinel_options_telemetry_v98.csv"
labeled_file = BASE / "spy_sentinel_options_labeled_v102.csv"

# ------------------------------------------
# CREDENTIALS
# ------------------------------------------

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

if not telemetry_file.exists():
    raise RuntimeError("Telemetry file not found")

# ------------------------------------------
# LOAD TELEMETRY
# ------------------------------------------

df = pd.read_csv(telemetry_file)

if df.empty:
    print("No telemetry rows available")
    raise SystemExit(0)

df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"],
    utc=True
)

# Create label columns if missing.
for col in [
    "spy_price_30m",
    "spy_return_30m",
    "spy_price_60m",
    "spy_return_60m",
    "spy_direction_60m",
    "label_status",
]:
    if col not in df.columns:
        df[col] = pd.NA

# ------------------------------------------
# ALPACA MARKET DATA
# ------------------------------------------

data_client = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY
)

now_utc = datetime.now(timezone.utc)

rows_labeled = 0

for idx, row in df.iterrows():

    ts = row["timestamp_utc"]

    if pd.isna(ts):
        continue

    # Only label when a full 60 minutes has passed.
    if now_utc < ts.to_pydatetime() + timedelta(minutes=60):
        if pd.isna(df.at[idx, "label_status"]):
            df.at[idx, "label_status"] = "WAITING"
        continue

    # Skip rows already labeled.
    current_status = df.at[idx, "label_status"]

    if (
        pd.notna(current_status)
        and current_status == "LABELED"
    ):
        continue

    start = ts.to_pydatetime()
    end = start + timedelta(minutes=70)

    req = StockBarsRequest(
        symbol_or_symbols=["SPY"],
        timeframe=TimeFrame(
            5,
            TimeFrameUnit.Minute
        ),
        start=start,
        end=end,
    )

    bars = data_client.get_stock_bars(req).df

    if bars.empty:
        df.at[idx, "label_status"] = "NO_DATA"
        continue

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == "SPY"]
    else:
        bars = bars.reset_index()

    if "timestamp" not in bars.columns:
        df.at[idx, "label_status"] = "NO_DATA"
        continue

    bars["timestamp"] = pd.to_datetime(
        bars["timestamp"],
        utc=True
    )

    def nearest_close(target_time):
        later = bars[
            bars["timestamp"] >= target_time
        ]

        if later.empty:
            return None

        r = later.iloc[0]

        delta = (
            r["timestamp"]
            - target_time
        ).total_seconds()

        # Refuse large gaps / overnight jumps.
        if delta > 10 * 60:
            return None

        return float(r["close"])

    price0 = float(row["spy_price"])

    target30 = ts + pd.Timedelta(minutes=30)
    target60 = ts + pd.Timedelta(minutes=60)

    price30 = nearest_close(target30)
    price60 = nearest_close(target60)

    if price30 is not None:
        ret30 = price30 / price0 - 1

        df.at[idx, "spy_price_30m"] = price30
        df.at[idx, "spy_return_30m"] = ret30

    if price60 is not None:
        ret60 = price60 / price0 - 1

        df.at[idx, "spy_price_60m"] = price60
        df.at[idx, "spy_return_60m"] = ret60

        if ret60 > 0:
            direction = "UP"
        elif ret60 < 0:
            direction = "DOWN"
        else:
            direction = "FLAT"

        df.at[idx, "spy_direction_60m"] = direction

    if (
        price30 is not None
        and price60 is not None
    ):
        df.at[idx, "label_status"] = "LABELED"
        rows_labeled += 1
    else:
        df.at[idx, "label_status"] = "INCOMPLETE"

# ------------------------------------------
# SAVE
# ------------------------------------------

df.to_csv(
    labeled_file,
    index=False
)

print("\nV102 LABELER")
print("Telemetry rows:", len(df))
print("New rows labeled:", rows_labeled)

print(
    "Total labeled:",
    int(
        (
            df["label_status"]
            == "LABELED"
        ).sum()
    )
)

print(
    "Waiting:",
    int(
        (
            df["label_status"]
            == "WAITING"
        ).sum()
    )
)

print(
    "Saved:",
    labeled_file.name
)

print("\nSAFETY")
print("READ-ONLY MARKET DATA")
print("NO ORDER SUBMISSION CODE")
print("PAPER EXECUTION UNCHANGED")
print("LIVE EXECUTION UNCHANGED")
