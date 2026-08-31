import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path.cwd()

options_file = BASE / "spy_sentinel_options_history_v111.csv"
spy_file = (
    Path.home()
    / "Documents"
    / "ai trading bot"
    / "SPY_5min_3years_clean.csv"
)

if not options_file.exists():
    raise RuntimeError("V105 options history not found")

if not spy_file.exists():
    raise RuntimeError("Verified SPY history not found")

print("\nV112 60-DAY LEAKAGE-SAFE OPTIONS FEATURE ENGINE")

# --------------------------------------------------
# 1. LOAD OPTIONS HISTORY
# --------------------------------------------------

opt = pd.read_csv(options_file)

opt["timestamp"] = pd.to_datetime(
    opt["timestamp"],
    utc=True
)

def parse_cp(symbol):
    s = str(symbol)

    # OCC symbol format:
    # SPY + YYMMDD + C/P + strike
    # C/P sits 9 chars from end.
    try:
        return s[-9]
    except:
        return None

opt["cp"] = opt["option_symbol"].apply(
    parse_cp
)

opt = opt[
    opt["cp"].isin(["C", "P"])
].copy()

print("Option rows:", len(opt))
print("Contracts:", opt["option_symbol"].nunique())

# --------------------------------------------------
# 2. OPTION RETURN / MOMENTUM
# --------------------------------------------------

opt = opt.sort_values(
    ["option_symbol", "timestamp"]
)

opt["option_ret_5m"] = (
    opt.groupby("option_symbol")["close"]
    .pct_change()
)

# --------------------------------------------------
# 3. AGGREGATE CALL / PUT ACTIVITY BY TIMESTAMP
# --------------------------------------------------

def agg_side(df, prefix):

    g = df.groupby("timestamp").agg(
        volume=("volume", "sum"),
        trades=("trade_count", "sum"),
        mean_close=("close", "mean"),
        mean_vwap=("vwap", "mean"),
        mean_ret5=("option_ret_5m", "mean"),
        contracts=("option_symbol", "nunique"),
    )

    return g.add_prefix(prefix)

calls = agg_side(
    opt[opt["cp"] == "C"],
    "call_"
)

puts = agg_side(
    opt[opt["cp"] == "P"],
    "put_"
)

features = calls.join(
    puts,
    how="outer"
).sort_index()

features = features.fillna(0)

# --------------------------------------------------
# 4. IMBALANCE FEATURES
# --------------------------------------------------

def safe_ratio(a, b):
    denom = a + b
    return np.where(
        denom != 0,
        (a - b) / denom,
        0.0
    )

features["volume_imbalance"] = safe_ratio(
    features["call_volume"],
    features["put_volume"]
)

features["trade_imbalance"] = safe_ratio(
    features["call_trades"],
    features["put_trades"]
)

features["contract_imbalance"] = safe_ratio(
    features["call_contracts"],
    features["put_contracts"]
)

features["momentum_imbalance"] = (
    features["call_mean_ret5"]
    - features["put_mean_ret5"]
)

features["vwap_imbalance"] = safe_ratio(
    features["call_mean_vwap"],
    features["put_mean_vwap"]
)

# --------------------------------------------------
# 5. LOAD VERIFIED SPY 5-MIN DATA
# --------------------------------------------------

spy = pd.read_csv(spy_file)

time_col = next(
    c for c in spy.columns
    if "time" in c.lower()
)

spy["timestamp"] = pd.to_datetime(
    spy[time_col],
    utc=True
)

spy = spy.sort_values("timestamp")

spy["date_et"] = (
    spy["timestamp"]
    .dt.tz_convert("America/New_York")
    .dt.date
)

# Same-day future labels only
for bars, label in [
    (6, "30m"),
    (12, "60m"),
]:

    future_close = spy["close"].shift(-bars)
    future_date = spy["date_et"].shift(-bars)

    spy[f"future_return_{label}"] = np.where(
        spy["date_et"] == future_date,
        future_close / spy["close"] - 1,
        np.nan
    )

spy["future_direction_60m"] = np.where(
    spy["future_return_60m"].notna(),
    (
        spy["future_return_60m"] > 0
    ).astype(int),
    np.nan
)

# --------------------------------------------------
# 6. ALIGN OPTIONS FEATURES TO SPY
# --------------------------------------------------

spy_keep = spy[
    [
        "timestamp",
        "close",
        "future_return_30m",
        "future_return_60m",
        "future_direction_60m",
    ]
].copy()

dataset = features.reset_index().merge(
    spy_keep,
    on="timestamp",
    how="inner",
    validate="one_to_one",
)

# --------------------------------------------------
# 7. CLEAN
# --------------------------------------------------

dataset = dataset.replace(
    [np.inf, -np.inf],
    np.nan
)

feature_cols = [
    "call_volume",
    "put_volume",
    "call_trades",
    "put_trades",
    "call_mean_close",
    "put_mean_close",
    "call_mean_vwap",
    "put_mean_vwap",
    "call_mean_ret5",
    "put_mean_ret5",
    "call_contracts",
    "put_contracts",
    "volume_imbalance",
    "trade_imbalance",
    "contract_imbalance",
    "momentum_imbalance",
    "vwap_imbalance",
]

usable = dataset.dropna(
    subset=feature_cols
    + [
        "future_return_30m",
        "future_return_60m",
        "future_direction_60m",
    ]
).copy()

# --------------------------------------------------
# 8. SAVE
# --------------------------------------------------

out_file = BASE / "spy_sentinel_options_features_v112.csv"

usable.to_csv(
    out_file,
    index=False
)

print("\nV112 RESULT")
print("Aligned rows:", len(dataset))
print("Usable labeled rows:", len(usable))
print("Feature count:", len(feature_cols))
print("Trading days:", pd.to_datetime(
    usable["timestamp"]
).dt.date.nunique())

print("Saved:", out_file.name)

print("\nNO MODEL TESTED")
print("NO HOLDOUT USED")
print("NO ORDER CODE")
print("PAPER/LIVE EXECUTION UNCHANGED")
