import pandas as pd
import numpy as np
from pathlib import Path

print("V7.1 TRUE THREE-YEAR WALK-FORWARD ENGINE")

DATA_FILE = Path(
    "/Users/ambrociojennings/Documents/ai trading bot/SPY_5min_3years_clean.csv"
)

raw = pd.read_csv(DATA_FILE)

print(f"Raw rows loaded: {len(raw)}")
print(f"Columns: {list(raw.columns)}")

time_col = next(
    c for c in raw.columns
    if "time" in c.lower() or "date" in c.lower()
)

raw["timestamp_utc"] = pd.to_datetime(
    raw[time_col],
    utc=True
)

raw = raw.sort_values(
    "timestamp_utc"
).copy()

raw["time_et"] = (
    raw["timestamp_utc"]
    .dt.tz_convert("America/New_York")
)

raw["date_et"] = raw["time_et"].dt.date

raw["minutes_et"] = (
    raw["time_et"].dt.hour * 60
    + raw["time_et"].dt.minute
)

clean3 = raw[
    (raw["minutes_et"] >= 570)
    & (raw["minutes_et"] < 960)
].copy()

print(f"Regular-session rows: {len(clean3)}")
print(f"Trading days: {clean3['date_et'].nunique()}")

clean3["ema9"] = (
    clean3["close"]
    .ewm(span=9, adjust=False)
    .mean()
)

clean3["ema21"] = (
    clean3["close"]
    .ewm(span=21, adjust=False)
    .mean()
)

delta = clean3["close"].diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.ewm(
    alpha=1/14,
    adjust=False
).mean()

avg_loss = loss.ewm(
    alpha=1/14,
    adjust=False
).mean()

rs = avg_gain / avg_loss.replace(0, np.nan)

clean3["rsi14"] = (
    100 - 100 / (1 + rs)
)

print("EMA and RSI features built")

typical_price = (
    clean3["high"]
    + clean3["low"]
    + clean3["close"]
) / 3

clean3["tpv"] = (
    typical_price * clean3["volume"]
)

clean3["cum_tpv"] = (
    clean3.groupby("date_et")["tpv"]
    .cumsum()
)

clean3["cum_volume"] = (
    clean3.groupby("date_et")["volume"]
    .cumsum()
)

clean3["vwap"] = (
    clean3["cum_tpv"]
    / clean3["cum_volume"]
)

clean3["volume_avg20"] = (
    clean3["volume"]
    .rolling(20)
    .mean()
    .shift(1)
)

clean3["volume_ratio"] = (
    clean3["volume"]
    / clean3["volume_avg20"]
)

print("VWAP and volume features built")

future_close = (
    clean3["close"].shift(-12)
)

future_date = (
    clean3["date_et"].shift(-12)
)

clean3["future_return_60m"] = np.where(
    clean3["date_et"] == future_date,
    future_close / clean3["close"] - 1,
    np.nan
)

print(
    "Same-day 60-minute forward returns built"
)

clean3["signal"] = "NO TRADE"

bull = (
    (clean3["ema9"] > clean3["ema21"])
    & (clean3["close"] > clean3["vwap"])
    & (clean3["rsi14"] >= 52)
)

bear = (
    (clean3["ema9"] < clean3["ema21"])
    & (clean3["close"] < clean3["vwap"])
    & (clean3["rsi14"] <= 48)
)

clean3.loc[bull, "signal"] = "BULLISH"
clean3.loc[bear, "signal"] = "BEARISH"

clean3 = clean3.dropna(
    subset=[
        "ema9",
        "ema21",
        "rsi14",
        "vwap",
        "volume_ratio",
        "future_return_60m",
    ]
).copy()

print(f"Usable research rows: {len(clean3)}")

days = sorted(
    clean3["date_et"].unique()
)

n_days = len(days)

train_end = int(n_days * 0.60)
val_end = int(n_days * 0.80)

train_days = days[:train_end]
validation_days = days[
    train_end:val_end
]
holdout_days = days[
    val_end:
]

train3 = clean3[
    clean3["date_et"].isin(train_days)
].copy()

validation3 = clean3[
    clean3["date_et"].isin(validation_days)
].copy()

holdout3 = clean3[
    clean3["date_et"].isin(holdout_days)
].copy()

print("\nTRUE THREE-YEAR SPLIT")
print(f"Train days:      {len(train_days)}")
print(f"Validation days: {len(validation_days)}")
print(f"Holdout days:    {len(holdout_days)}")

print("\nPERIOD DATE RANGES")

for name, frame in [
    ("TRAIN", train3),
    ("VALIDATION", validation3),
    ("HOLDOUT", holdout3),
]:

    print(
        f"{name}: "
        f"{frame['date_et'].min()} -> "
        f"{frame['date_et'].max()} | "
        f"{frame['date_et'].nunique()} days | "
        f"{len(frame)} rows"
    )

print("\nV7.1 FRAMEWORK STATUS")

coverage_days = (
    pd.Timestamp(clean3["date_et"].max())
    - pd.Timestamp(clean3["date_et"].min())
).days

print(f"Calendar coverage: {coverage_days} days")
print(
    f"Approx years: "
    f"{coverage_days / 365.25:.2f}"
)

print("HOLDOUT DESIGNATED AND SEALED")
print("NO HOLDOUT STRATEGY RESULTS INSPECTED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

clean3.to_csv(
    "spy_sentinel_true_3year_research_base.csv",
    index=False
)

print("True 3-year research base saved")

print("\nV7.2 PURGED THREE-YEAR SPLIT")

PURGE_BARS = 12

train3_purged = train3.iloc[
    :-PURGE_BARS
].copy()

validation3_purged = validation3.iloc[
    :-PURGE_BARS
].copy()

holdout3_sealed = holdout3.copy()

print(f"Purged bars per boundary: {PURGE_BARS}")
print(f"Train rows:      {len(train3_purged)}")
print(f"Validation rows: {len(validation3_purged)}")
print(f"Holdout rows:    {len(holdout3_sealed)}")

print("\nPURGED DATE CHECK")

for name, frame in [
    ("TRAIN", train3_purged),
    ("VALIDATION", validation3_purged),
]:

    print(
        f"{name}: "
        f"{frame['date_et'].min()} -> "
        f"{frame['date_et'].max()} | "
        f"{frame['date_et'].nunique()} days"
    )

print(
    "HOLDOUT dates retained but "
    "performance remains uninspected"
)

def evaluate_signal_v72(
    frame,
    signal_col="signal"
):

    sample = frame[
        frame[signal_col].isin(
            ["BULLISH", "BEARISH"]
        )
    ].dropna(
        subset=["future_return_60m"]
    ).copy()

    if sample.empty:
        return {
            "signals": 0,
            "accuracy": 0.0,
            "avg_return": 0.0,
        }

    wins = (
        (
            (sample[signal_col] == "BULLISH")
            & (sample["future_return_60m"] > 0)
        )
        |
        (
            (sample[signal_col] == "BEARISH")
            & (sample["future_return_60m"] < 0)
        )
    )

    directional_return = np.where(
        sample[signal_col] == "BULLISH",
        sample["future_return_60m"],
        -sample["future_return_60m"]
    )

    return {
        "signals": len(sample),
        "accuracy": wins.mean() * 100,
        "avg_return": (
            float(np.mean(directional_return))
            * 100
        ),
    }

print("Purged evaluator ready")

print("\nTRUE 3-YEAR BASELINE")

train_baseline = evaluate_signal_v72(
    train3_purged
)

validation_baseline = evaluate_signal_v72(
    validation3_purged
)

print(
    f"TRAIN: "
    f"{train_baseline['accuracy']:.2f}% | "
    f"{train_baseline['signals']} signals | "
    f"avg {train_baseline['avg_return']:+.4f}%"
)

print(
    f"VALIDATION: "
    f"{validation_baseline['accuracy']:.2f}% | "
    f"{validation_baseline['signals']} signals | "
    f"avg {validation_baseline['avg_return']:+.4f}%"
)

def wilson_low_v72(
    accuracy_pct,
    n,
    z=1.96
):

    if n <= 0:
        return 0.0

    p = accuracy_pct / 100.0

    denominator = (
        1 + z**2 / n
    )

    center = (
        p + z**2 / (2 * n)
    ) / denominator

    margin = (
        z * np.sqrt(
            p * (1 - p) / n
            + z**2 / (4 * n**2)
        )
        / denominator
    )

    return (
        center - margin
    ) * 100

validation_ci_low = wilson_low_v72(
    validation_baseline["accuracy"],
    validation_baseline["signals"]
)

print(
    f"Validation 95% CI low: "
    f"{validation_ci_low:.2f}%"
)

baseline_candidate = (
    train_baseline["signals"] >= 500
    and validation_baseline["signals"] >= 150
    and train_baseline["accuracy"] >= 53
    and validation_baseline["accuracy"] >= 55
    and train_baseline["avg_return"] > 0
    and validation_baseline["avg_return"] > 0
    and validation_ci_low > 50
)

print("\nV7.2 BASELINE GATE")
print(
    f"Baseline qualifies: "
    f"{baseline_candidate}"
)

print("\nV7.2 RESEARCH DISCIPLINE")

if baseline_candidate:
    baseline_verdict = (
        "BASE SIGNAL MAY PROCEED TO FROZEN TEST"
    )
else:
    baseline_verdict = (
        "BASE SIGNAL DOES NOT QUALIFY"
    )

print(f"Verdict: {baseline_verdict}")
print("TRAIN + VALIDATION ONLY WERE EVALUATED")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([
    {
        "period": "TRAIN",
        **train_baseline,
    },
    {
        "period": "VALIDATION",
        **validation_baseline,
    },
]).to_csv(
    "spy_sentinel_true3year_baseline_v72.csv",
    index=False
)

print(
    "Purged 3-year baseline results saved"
)

print("\nV7.3 TRUE 3-YEAR FILTER SCREEN")

for frame in [
    train3_purged,
    validation3_purged,
]:

    frame["mom30_lag"] = (
        frame["close"]
        .pct_change(6)
        .shift(1)
    )

    frame["mom30_match"] = (
        (
            (frame["signal"] == "BULLISH")
            & (frame["mom30_lag"] > 0)
        )
        |
        (
            (frame["signal"] == "BEARISH")
            & (frame["mom30_lag"] < 0)
        )
    )

print("Lagged momentum confirmation created")

FILTERS_V73 = [
    "BASE",
    "VOLUME_1_2",
    "RSI_STRONG",
    "MOM30_CONFIRM",
    "MORNING",
    "AFTERNOON",
]

def apply_filter_v73(frame, name):

    sample = frame[
        frame["signal"].isin(
            ["BULLISH", "BEARISH"]
        )
    ].copy()

    if name == "VOLUME_1_2":
        sample = sample[
            sample["volume_ratio"] >= 1.2
        ]

    elif name == "RSI_STRONG":

        sample = sample[
            (
                (sample["signal"] == "BULLISH")
                & (sample["rsi14"] >= 55)
            )
            |
            (
                (sample["signal"] == "BEARISH")
                & (sample["rsi14"] <= 45)
            )
        ]

    elif name == "MOM30_CONFIRM":
        sample = sample[
            sample["mom30_match"]
        ]

    elif name == "MORNING":
        sample = sample[
            sample["minutes_et"] < 660
        ]

    elif name == "AFTERNOON":
        sample = sample[
            sample["minutes_et"] >= 810
        ]

    return sample

filter_rows_v73 = []

for name in FILTERS_V73:

    tr_frame = apply_filter_v73(
        train3_purged,
        name
    )

    va_frame = apply_filter_v73(
        validation3_purged,
        name
    )

    tr = evaluate_signal_v72(
        tr_frame
    )

    va = evaluate_signal_v72(
        va_frame
    )

    filter_rows_v73.append({
        "filter": name,
        "train_signals": tr["signals"],
        "train_accuracy": tr["accuracy"],
        "train_avg_return": tr["avg_return"],
        "val_signals": va["signals"],
        "val_accuracy": va["accuracy"],
        "val_avg_return": va["avg_return"],
        "accuracy_gap": abs(
            tr["accuracy"]
            - va["accuracy"]
        ),
    })

filter_df_v73 = pd.DataFrame(
    filter_rows_v73
)

print("\nTRUE 3-YEAR FILTER RESULTS")
print(filter_df_v73.to_string(index=False))

filter_df_v73["val_ci_low"] = (
    filter_df_v73.apply(
        lambda r: wilson_low_v72(
            r["val_accuracy"],
            int(r["val_signals"])
        ),
        axis=1
    )
)

print("\nVALIDATION CONFIDENCE")

print(
    filter_df_v73[
        [
            "filter",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "val_avg_return",
        ]
    ].to_string(index=False)
)

filter_df_v73["strict_pass"] = (
    (filter_df_v73["train_signals"] >= 300)
    & (filter_df_v73["val_signals"] >= 100)
    & (filter_df_v73["train_accuracy"] >= 53)
    & (filter_df_v73["val_accuracy"] >= 55)
    & (filter_df_v73["train_avg_return"] > 0)
    & (filter_df_v73["val_avg_return"] > 0)
    & (filter_df_v73["accuracy_gap"] <= 8)
    & (filter_df_v73["val_ci_low"] > 50)
)

print("\nV7.3 STRICT FILTER GATE")

print(
    filter_df_v73[
        [
            "filter",
            "train_accuracy",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "strict_pass",
        ]
    ].to_string(index=False)
)

eligible_v73 = filter_df_v73[
    filter_df_v73["strict_pass"]
].copy()

print("\nV7.3 CANDIDATE SELECTION")

if not eligible_v73.empty:

    winner_v73 = (
        eligible_v73
        .sort_values(
            [
                "val_ci_low",
                "val_accuracy",
                "val_signals",
            ],
            ascending=False
        )
        .iloc[0]
    )

    frozen_filter_v73 = (
        winner_v73["filter"]
    )

    verdict_v73 = (
        "FREEZE FILTER FOR HOLDOUT TEST"
    )

    print(
        f"Frozen candidate: "
        f"{frozen_filter_v73}"
    )

else:

    frozen_filter_v73 = "NONE"

    verdict_v73 = (
        "NO TRUE-3YR FILTER SURVIVES"
    )

print(f"Verdict: {verdict_v73}")

print("\nRESEARCH SAFETY STATUS")
print("ONLY PREDEFINED FILTERS WERE TESTED")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("NO FILTER WAS TUNED TO HOLDOUT")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

filter_df_v73.to_csv(
    "spy_sentinel_true3year_filter_screen_v73.csv",
    index=False
)

pd.DataFrame([{
    "frozen_filter": frozen_filter_v73,
    "verdict": verdict_v73,
}]).to_csv(
    "spy_sentinel_true3year_candidate_v73.csv",
    index=False
)

print("True 3-year filter screen saved")

print("\nV7.4 TRUE 3-YEAR FIRST-HOUR TEST")

def first_hour_map_v74(frame):

    morning = frame[
        (frame["minutes_et"] >= 570)
        & (frame["minutes_et"] <= 630)
    ].copy()

    daily = (
        morning.groupby("date_et")
        .agg(
            first_open=("open", "first"),
            hour_close=("close", "last"),
        )
    )

    daily["first_hour_return"] = (
        daily["hour_close"]
        / daily["first_open"]
        - 1
    )

    return daily["first_hour_return"].to_dict()

train_fh_map = first_hour_map_v74(
    train3_purged
)

validation_fh_map = first_hour_map_v74(
    validation3_purged
)

print("First-hour daily returns built")

for frame, mapping in [
    (train3_purged, train_fh_map),
    (validation3_purged, validation_fh_map),
]:

    frame["first_hour_return_v74"] = (
        frame["date_et"].map(mapping)
    )

print(
    f"Train first-hour days: "
    f"{len(train_fh_map)}"
)

print(
    f"Validation first-hour days: "
    f"{len(validation_fh_map)}"
)

FH_STRATEGIES_V74 = [
    "FIRST_HOUR_CONTINUE",
    "FIRST_HOUR_FADE",
]

def build_fh_signal_v74(frame, name):

    sample = frame[
        frame["minutes_et"] == 630
    ].copy()

    sample["fh_signal_v74"] = "NO TRADE"

    positive = (
        sample["first_hour_return_v74"] > 0
    )

    negative = (
        sample["first_hour_return_v74"] < 0
    )

    if name == "FIRST_HOUR_CONTINUE":

        sample.loc[
            positive,
            "fh_signal_v74"
        ] = "BULLISH"

        sample.loc[
            negative,
            "fh_signal_v74"
        ] = "BEARISH"

    elif name == "FIRST_HOUR_FADE":

        sample.loc[
            positive,
            "fh_signal_v74"
        ] = "BEARISH"

        sample.loc[
            negative,
            "fh_signal_v74"
        ] = "BULLISH"

    return sample

fh_rows_v74 = []

for name in FH_STRATEGIES_V74:

    tr_frame = build_fh_signal_v74(
        train3_purged,
        name
    )

    va_frame = build_fh_signal_v74(
        validation3_purged,
        name
    )

    tr = evaluate_signal_v72(
        tr_frame,
        "fh_signal_v74"
    )

    va = evaluate_signal_v72(
        va_frame,
        "fh_signal_v74"
    )

    fh_rows_v74.append({
        "strategy": name,
        "train_signals": tr["signals"],
        "train_accuracy": tr["accuracy"],
        "train_avg_return": tr["avg_return"],
        "val_signals": va["signals"],
        "val_accuracy": va["accuracy"],
        "val_avg_return": va["avg_return"],
        "accuracy_gap": abs(
            tr["accuracy"]
            - va["accuracy"]
        ),
    })

fh_df_v74 = pd.DataFrame(
    fh_rows_v74
)

print("\nFIRST-HOUR RESULTS")
print(fh_df_v74.to_string(index=False))

fh_df_v74["val_ci_low"] = (
    fh_df_v74.apply(
        lambda r: wilson_low_v72(
            r["val_accuracy"],
            int(r["val_signals"])
        ),
        axis=1
    )
)

print("\nFIRST-HOUR CONFIDENCE")

print(
    fh_df_v74[
        [
            "strategy",
            "train_accuracy",
            "val_accuracy",
            "val_ci_low",
            "train_signals",
            "val_signals",
            "val_avg_return",
        ]
    ].to_string(index=False)
)

fh_df_v74["val_ci_low"] = (
    fh_df_v74.apply(
        lambda r: wilson_low_v72(
            r["val_accuracy"],
            int(r["val_signals"])
        ),
        axis=1
    )
)

print("\nFIRST-HOUR CONFIDENCE")

print(
    fh_df_v74[
        [
            "strategy",
            "train_accuracy",
            "val_accuracy",
            "val_ci_low",
            "train_signals",
            "val_signals",
            "val_avg_return",
        ]
    ].to_string(index=False)
)

fh_df_v74["strict_pass"] = (
    (fh_df_v74["train_signals"] >= 300)
    & (fh_df_v74["val_signals"] >= 100)
    & (fh_df_v74["train_accuracy"] >= 53)
    & (fh_df_v74["val_accuracy"] >= 55)
    & (fh_df_v74["train_avg_return"] > 0)
    & (fh_df_v74["val_avg_return"] > 0)
    & (fh_df_v74["accuracy_gap"] <= 8)
    & (fh_df_v74["val_ci_low"] > 50)
)

print("\nV7.4 STRICT GATE")

print(
    fh_df_v74[
        [
            "strategy",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "val_avg_return",
            "strict_pass",
        ]
    ].to_string(index=False)
)

fh_eligible_v74 = fh_df_v74[
    fh_df_v74["strict_pass"]
].copy()

print("\nV7.4 CANDIDATE SELECTION")

if not fh_eligible_v74.empty:

    fh_winner_v74 = (
        fh_eligible_v74
        .sort_values(
            [
                "val_ci_low",
                "val_accuracy",
            ],
            ascending=False
        )
        .iloc[0]
    )

    frozen_fh_v74 = (
        fh_winner_v74["strategy"]
    )

    verdict_fh_v74 = (
        "FREEZE FIRST-HOUR STRATEGY FOR HOLDOUT"
    )

    print(
        f"Frozen candidate: "
        f"{frozen_fh_v74}"
    )

else:

    frozen_fh_v74 = "NONE"

    verdict_fh_v74 = (
        "NO FIRST-HOUR STRATEGY SURVIVES"
    )

print(f"Verdict: {verdict_fh_v74}")

fh_eligible_v74 = fh_df_v74[
    fh_df_v74["strict_pass"]
].copy()

print("\nV7.4 CANDIDATE SELECTION")

if not fh_eligible_v74.empty:

    fh_winner_v74 = (
        fh_eligible_v74
        .sort_values(
            [
                "val_ci_low",
                "val_accuracy",
            ],
            ascending=False
        )
        .iloc[0]
    )

    frozen_fh_v74 = (
        fh_winner_v74["strategy"]
    )

    verdict_fh_v74 = (
        "FREEZE FIRST-HOUR STRATEGY FOR HOLDOUT"
    )

    print(
        f"Frozen candidate: "
        f"{frozen_fh_v74}"
    )

else:

    frozen_fh_v74 = "NONE"

    verdict_fh_v74 = (
        "NO FIRST-HOUR STRATEGY SURVIVES"
    )

print(f"Verdict: {verdict_fh_v74}")

print("\nRESEARCH SAFETY STATUS")
print("ONE OPPORTUNITY PER TRADING DAY")
print("NO MAGNITUDE THRESHOLD WAS TUNED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

fh_df_v74.to_csv(
    "spy_sentinel_true3year_first_hour_v74.csv",
    index=False
)

pd.DataFrame([{
    "frozen_strategy": frozen_fh_v74,
    "verdict": verdict_fh_v74,
}]).to_csv(
    "spy_sentinel_true3year_first_hour_candidate_v74.csv",
    index=False
)

print("True 3-year first-hour research saved")

print("\nV7.5 TRUE 3-YEAR ML DEVELOPMENT")

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
)

print("ML libraries loaded")

for frame in [
    train3_purged,
    validation3_purged,
]:

    frame["mom15_ml"] = (
        frame["close"]
        .pct_change(3)
        .shift(1)
    )

    frame["mom30_ml"] = (
        frame["close"]
        .pct_change(6)
        .shift(1)
    )

    frame["mom60_ml"] = (
        frame["close"]
        .pct_change(12)
        .shift(1)
    )

    frame["ema_spread_ml"] = (
        (frame["ema9"] - frame["ema21"])
        / frame["close"]
    )

    frame["vwap_distance_ml"] = (
        (frame["close"] - frame["vwap"])
        / frame["close"]
    )

    frame["minute_ml"] = (
        frame["minutes_et"]
    )

print("Lagged ML features created")

ML_FEATURES_V75 = [
    "rsi14",
    "volume_ratio",
    "mom15_ml",
    "mom30_ml",
    "mom60_ml",
    "ema_spread_ml",
    "vwap_distance_ml",
    "minute_ml",
]

def prepare_ml_v75(frame):

    data = frame.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna(
        subset=ML_FEATURES_V75
        + ["future_return_60m"]
    ).copy()

    data["target_ml"] = (
        data["future_return_60m"] > 0
    ).astype(int)

    return data

ml_train = prepare_ml_v75(
    train3_purged
)

ml_validation = prepare_ml_v75(
    validation3_purged
)

print(f"ML train rows: {len(ml_train)}")
print(f"ML validation rows: {len(ml_validation)}")

print("\nTRAIN-PERIOD TIME-SERIES CV")

X_train_all = ml_train[
    ML_FEATURES_V75
]

y_train_all = ml_train[
    "target_ml"
]

tscv_v75 = TimeSeriesSplit(
    n_splits=5
)

cv_rows_v75 = []

for fold, (tr_idx, te_idx) in enumerate(
    tscv_v75.split(X_train_all),
    start=1
):

    X_tr = X_train_all.iloc[tr_idx]
    X_te = X_train_all.iloc[te_idx]

    y_tr = y_train_all.iloc[tr_idx]
    y_te = y_train_all.iloc[te_idx]

    model = Pipeline([
        ("scale", StandardScaler()),
        (
            "logistic",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            )
        ),
    ])

    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)
    prob = model.predict_proba(X_te)[:, 1]

    acc = accuracy_score(
        y_te,
        pred
    ) * 100

    bal = balanced_accuracy_score(
        y_te,
        pred
    ) * 100

    auc = roc_auc_score(
        y_te,
        prob
    ) * 100

    cv_rows_v75.append({
        "fold": fold,
        "accuracy": acc,
        "balanced_accuracy": bal,
        "auc": auc,
    })

    print(
        f"Fold {fold}: "
        f"acc {acc:.2f}% | "
        f"bal {bal:.2f}% | "
        f"AUC {auc:.2f}%"
    )

cv_df_v75 = pd.DataFrame(
    cv_rows_v75
)

cv_mean_bal = (
    cv_df_v75["balanced_accuracy"].mean()
)

cv_worst_bal = (
    cv_df_v75["balanced_accuracy"].min()
)

cv_mean_auc = (
    cv_df_v75["auc"].mean()
)

print("\nTRAIN CV STABILITY")

print(
    f"Mean balanced accuracy: "
    f"{cv_mean_bal:.2f}%"
)

print(
    f"Worst balanced accuracy: "
    f"{cv_worst_bal:.2f}%"
)

print(
    f"Mean AUC: "
    f"{cv_mean_auc:.2f}%"
)

print("\nSEPARATE VALIDATION TEST")

final_model_v75 = Pipeline([
    ("scale", StandardScaler()),
    (
        "logistic",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )
    ),
])

final_model_v75.fit(
    ml_train[ML_FEATURES_V75],
    ml_train["target_ml"]
)

val_prob_v75 = (
    final_model_v75.predict_proba(
        ml_validation[ML_FEATURES_V75]
    )[:, 1]
)

val_pred_v75 = (
    val_prob_v75 >= 0.50
).astype(int)

val_acc_v75 = accuracy_score(
    ml_validation["target_ml"],
    val_pred_v75
) * 100

val_bal_v75 = balanced_accuracy_score(
    ml_validation["target_ml"],
    val_pred_v75
) * 100

val_auc_v75 = roc_auc_score(
    ml_validation["target_ml"],
    val_prob_v75
) * 100

print(f"Validation accuracy: {val_acc_v75:.2f}%")
print(f"Validation balanced accuracy: {val_bal_v75:.2f}%")
print(f"Validation AUC: {val_auc_v75:.2f}%")

print("\nHIGH-CONFIDENCE VALIDATION TEST")

selected_v75 = (
    (val_prob_v75 >= 0.55)
    | (val_prob_v75 <= 0.45)
)

selected_probs_v75 = (
    val_prob_v75[selected_v75]
)

selected_actual_v75 = (
    ml_validation["target_ml"]
    .to_numpy()[selected_v75]
)

if len(selected_probs_v75):

    selected_pred_v75 = (
        selected_probs_v75 >= 0.50
    ).astype(int)

    hc_accuracy_v75 = (
        selected_pred_v75
        == selected_actual_v75
    ).mean() * 100

else:

    hc_accuracy_v75 = 0.0

hc_signals_v75 = len(
    selected_probs_v75
)

print(
    f"High-confidence signals: "
    f"{hc_signals_v75}"
)

print(
    f"High-confidence accuracy: "
    f"{hc_accuracy_v75:.2f}%"
)

print("\nV7.5 ML GATE")

ml_candidate_v75 = (
    cv_mean_bal >= 52
    and cv_worst_bal >= 48
    and cv_mean_auc >= 52
    and val_bal_v75 >= 52
    and val_auc_v75 >= 52
    and hc_signals_v75 >= 150
    and hc_accuracy_v75 >= 55
)

if ml_candidate_v75:
    ml_verdict_v75 = (
        "FREEZE ML MODEL FOR HOLDOUT TEST"
    )
else:
    ml_verdict_v75 = (
        "TRUE-3YR ML MODEL NOT STRONG ENOUGH"
    )

print(f"Verdict: {ml_verdict_v75}")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("NO HOLDOUT TRAINING OR TUNING")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

cv_df_v75.to_csv(
    "spy_sentinel_true3year_ml_cv_v75.csv",
    index=False
)

print("True 3-year ML research saved")

print("\nV7.6 NONLINEAR MODEL SCREEN")

from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
)

NONLINEAR_MODELS = [
    "RANDOM_FOREST",
    "HIST_GRADIENT_BOOSTING",
]

print("Two predefined nonlinear models loaded")

def make_model_v76(name):

    if name == "RANDOM_FOREST":

        return RandomForestClassifier(
            n_estimators=400,
            max_depth=6,
            min_samples_leaf=30,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

    if name == "HIST_GRADIENT_BOOSTING":

        return HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=200,
            max_leaf_nodes=15,
            min_samples_leaf=30,
            l2_regularization=1.0,
            random_state=42,
        )

    raise ValueError(name)

nonlinear_rows_v76 = []

print("\nTRAIN-PERIOD NONLINEAR CV")

for model_name in NONLINEAR_MODELS:

    fold_bal = []
    fold_auc = []

    for fold, (tr_idx, te_idx) in enumerate(
        tscv_v75.split(X_train_all),
        start=1
    ):

        X_tr = X_train_all.iloc[tr_idx]
        X_te = X_train_all.iloc[te_idx]

        y_tr = y_train_all.iloc[tr_idx]
        y_te = y_train_all.iloc[te_idx]

        model = make_model_v76(
            model_name
        )

        model.fit(
            X_tr,
            y_tr
        )

        pred = model.predict(
            X_te
        )

        prob = model.predict_proba(
            X_te
        )[:, 1]

        bal = balanced_accuracy_score(
            y_te,
            pred
        ) * 100

        auc = roc_auc_score(
            y_te,
            prob
        ) * 100

        fold_bal.append(bal)
        fold_auc.append(auc)

    print(
        f"{model_name}: "
        f"mean bal {np.mean(fold_bal):.2f}% | "
        f"worst bal {np.min(fold_bal):.2f}% | "
        f"mean AUC {np.mean(fold_auc):.2f}%"
    )

    nonlinear_rows_v76.append({
        "model": model_name,
        "cv_mean_bal": np.mean(fold_bal),
        "cv_worst_bal": np.min(fold_bal),
        "cv_mean_auc": np.mean(fold_auc),
    })

print("\nNONLINEAR SEPARATE VALIDATION")

for row in nonlinear_rows_v76:

    model_name = row["model"]

    model = make_model_v76(
        model_name
    )

    model.fit(
        ml_train[ML_FEATURES_V75],
        ml_train["target_ml"]
    )

    val_prob = model.predict_proba(
        ml_validation[ML_FEATURES_V75]
    )[:, 1]

    val_pred = (
        val_prob >= 0.50
    ).astype(int)

    row["val_accuracy"] = (
        accuracy_score(
            ml_validation["target_ml"],
            val_pred
        ) * 100
    )

    row["val_balanced"] = (
        balanced_accuracy_score(
            ml_validation["target_ml"],
            val_pred
        ) * 100
    )

    row["val_auc"] = (
        roc_auc_score(
            ml_validation["target_ml"],
            val_prob
        ) * 100
    )

    print(
        f"{model_name}: "
        f"acc {row['val_accuracy']:.2f}% | "
        f"bal {row['val_balanced']:.2f}% | "
        f"AUC {row['val_auc']:.2f}%"
    )

    row["_val_prob"] = val_prob

print("\nNONLINEAR HIGH-CONFIDENCE TEST")

for row in nonlinear_rows_v76:

    val_prob = row.pop(
        "_val_prob"
    )

    selected = (
        (val_prob >= 0.55)
        | (val_prob <= 0.45)
    )

    probs = val_prob[selected]

    actual = (
        ml_validation["target_ml"]
        .to_numpy()[selected]
    )

    if len(probs):

        pred = (
            probs >= 0.50
        ).astype(int)

        hc_accuracy = (
            pred == actual
        ).mean() * 100

    else:

        hc_accuracy = 0.0

    row["hc_signals"] = len(probs)
    row["hc_accuracy"] = hc_accuracy

    print(
        f"{row['model']}: "
        f"{len(probs)} signals | "
        f"{hc_accuracy:.2f}% accuracy"
    )

nonlinear_df_v76 = pd.DataFrame(
    nonlinear_rows_v76
)

nonlinear_df_v76["strict_pass"] = (
    (nonlinear_df_v76["cv_mean_bal"] >= 52)
    & (nonlinear_df_v76["cv_worst_bal"] >= 48)
    & (nonlinear_df_v76["cv_mean_auc"] >= 52)
    & (nonlinear_df_v76["val_balanced"] >= 52)
    & (nonlinear_df_v76["val_auc"] >= 52)
    & (nonlinear_df_v76["hc_signals"] >= 150)
    & (nonlinear_df_v76["hc_accuracy"] >= 55)
)

print("\nV7.6 NONLINEAR STRICT GATE")

print(
    nonlinear_df_v76[
        [
            "model",
            "cv_mean_bal",
            "cv_worst_bal",
            "val_balanced",
            "val_auc",
            "hc_signals",
            "hc_accuracy",
            "strict_pass",
        ]
    ].to_string(index=False)
)

eligible_v76 = nonlinear_df_v76[
    nonlinear_df_v76["strict_pass"]
].copy()

print("\nV7.6 CANDIDATE SELECTION")

if not eligible_v76.empty:

    winner_v76 = (
        eligible_v76.sort_values(
            [
                "val_auc",
                "val_balanced",
                "hc_accuracy",
            ],
            ascending=False
        ).iloc[0]
    )

    frozen_model_v76 = (
        winner_v76["model"]
    )

    verdict_v76 = (
        "FREEZE NONLINEAR MODEL FOR HOLDOUT"
    )

    print(
        f"Frozen candidate: "
        f"{frozen_model_v76}"
    )

else:

    frozen_model_v76 = "NONE"

    verdict_v76 = (
        "NO NONLINEAR MODEL SURVIVES"
    )

print(f"Verdict: {verdict_v76}")

print("\nRESEARCH SAFETY STATUS")
print("ONLY TWO PREDEFINED MODEL FAMILIES TESTED")
print("TRAIN CV + SEPARATE VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("NO HOLDOUT TRAINING OR TUNING")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

nonlinear_df_v76.to_csv(
    "spy_sentinel_true3year_nonlinear_v76.csv",
    index=False
)

pd.DataFrame([{
    "frozen_model": frozen_model_v76,
    "verdict": verdict_v76,
}]).to_csv(
    "spy_sentinel_true3year_nonlinear_candidate_v76.csv",
    index=False
)

print("Nonlinear research saved")

print("\nV7.7 TRAIN-ONLY REGIME DISCOVERY")

for frame in [
    train3_purged,
    validation3_purged,
]:

    high_low = (
        frame["high"] - frame["low"]
    )

    high_close = (
        frame["high"]
        - frame["close"].shift(1)
    ).abs()

    low_close = (
        frame["low"]
        - frame["close"].shift(1)
    ).abs()

    frame["true_range_v77"] = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    frame["atr14_v77"] = (
        frame["true_range_v77"]
        .rolling(14)
        .mean()
        .shift(1)
    )

    frame["atr_pct_v77"] = (
        frame["atr14_v77"]
        / frame["close"]
    )

print("Lagged volatility features created")

TRAIN_ATR_MEDIAN_V77 = (
    train3_purged[
        "atr_pct_v77"
    ].median()
)

for frame in [
    train3_purged,
    validation3_purged,
]:

    frame["trend_v77"] = np.where(
        frame["ema9"] > frame["ema21"],
        "UPTREND",
        "DOWNTREND"
    )

    frame["vol_v77"] = np.where(
        frame["atr_pct_v77"]
        >= TRAIN_ATR_MEDIAN_V77,
        "HIGH_VOL",
        "LOW_VOL"
    )

    frame["session_v77"] = np.where(
        frame["minutes_et"] < 660,
        "MORNING",
        np.where(
            frame["minutes_et"] < 810,
            "MIDDAY",
            "AFTERNOON"
        )
    )

print(
    f"Frozen TRAIN volatility median: "
    f"{TRAIN_ATR_MEDIAN_V77:.6f}"
)

def one_per_day_bucket_v77(frame):

    usable = frame.dropna(
        subset=[
            "future_return_60m",
            "atr_pct_v77",
        ]
    ).copy()

    usable["bucket_v77"] = (
        usable["trend_v77"]
        + "|"
        + usable["vol_v77"]
        + "|"
        + usable["session_v77"]
    )

    one_per_day = (
        usable
        .sort_values("time_et")
        .groupby(
            ["date_et", "bucket_v77"],
            as_index=False
        )
        .first()
    )

    return one_per_day

train_bucket_v77 = (
    one_per_day_bucket_v77(
        train3_purged
    )
)

validation_bucket_v77 = (
    one_per_day_bucket_v77(
        validation3_purged
    )
)

print(
    f"Train one-per-day bucket rows: "
    f"{len(train_bucket_v77)}"
)

train_regimes_v77 = (
    train_bucket_v77
    .groupby("bucket_v77")
    .agg(
        observations=(
            "future_return_60m",
            "size"
        ),
        up_rate=(
            "future_return_60m",
            lambda x: (
                (x > 0).mean() * 100
            )
        ),
        avg_return=(
            "future_return_60m",
            lambda x: (
                x.mean() * 100
            )
        ),
    )
    .reset_index()
)

train_regimes_v77[
    "directional_edge"
] = abs(
    train_regimes_v77["up_rate"]
    - 50
)

train_regimes_v77[
    "frozen_direction"
] = np.where(
    train_regimes_v77["up_rate"] >= 50,
    "BULLISH",
    "BEARISH"
)

print("\nTRAIN-ONLY REGIME TABLE")

print(
    train_regimes_v77
    .sort_values(
        "directional_edge",
        ascending=False
    )
    .to_string(index=False)
)

candidate_pool_v77 = (
    train_regimes_v77[
        train_regimes_v77[
            "observations"
        ] >= 100
    ]
    .sort_values(
        [
            "directional_edge",
            "observations",
        ],
        ascending=False
    )
    .head(3)
    .copy()
)

print("\nFROZEN TRAIN CANDIDATES")

print(
    candidate_pool_v77.to_string(
        index=False
    )
)

print(
    f"Candidate count: "
    f"{len(candidate_pool_v77)}"
)

validation_rows_v77 = []

for _, candidate in (
    candidate_pool_v77.iterrows()
):

    bucket_name = (
        candidate["bucket_v77"]
    )

    direction = (
        candidate["frozen_direction"]
    )

    sample = validation_bucket_v77[
        validation_bucket_v77[
            "bucket_v77"
        ] == bucket_name
    ].copy()

    if direction == "BULLISH":

        wins = (
            sample[
                "future_return_60m"
            ] > 0
        )

        signed_return = (
            sample[
                "future_return_60m"
            ]
        )

    else:

        wins = (
            sample[
                "future_return_60m"
            ] < 0
        )

        signed_return = (
            -sample[
                "future_return_60m"
            ]
        )

    validation_rows_v77.append({
        "bucket": bucket_name,
        "direction": direction,
        "train_observations": int(
            candidate["observations"]
        ),
        "train_edge": float(
            candidate["directional_edge"]
        ),
        "val_observations": len(sample),
        "val_accuracy": (
            wins.mean() * 100
            if len(sample)
            else 0.0
        ),
        "val_avg_return": (
            signed_return.mean() * 100
            if len(sample)
            else 0.0
        ),
    })

validation_regimes_v77 = pd.DataFrame(
    validation_rows_v77
)

print("\nFROZEN REGIME VALIDATION")

print(
    validation_regimes_v77.to_string(
        index=False
    )
)

validation_regimes_v77[
    "val_ci_low"
] = (
    validation_regimes_v77.apply(
        lambda r: wilson_low_v72(
            r["val_accuracy"],
            int(r["val_observations"])
        ),
        axis=1
    )
)

validation_regimes_v77[
    "strict_pass"
] = (
    (
        validation_regimes_v77[
            "val_observations"
        ] >= 50
    )
    & (
        validation_regimes_v77[
            "val_accuracy"
        ] >= 55
    )
    & (
        validation_regimes_v77[
            "val_avg_return"
        ] > 0
    )
    & (
        validation_regimes_v77[
            "val_ci_low"
        ] > 50
    )
)

print("\nV7.7 REGIME VALIDATION GATE")

print(
    validation_regimes_v77[
        [
            "bucket",
            "direction",
            "val_observations",
            "val_accuracy",
            "val_ci_low",
            "val_avg_return",
            "strict_pass",
        ]
    ].to_string(index=False)
)

survivors_v77 = (
    validation_regimes_v77[
        validation_regimes_v77[
            "strict_pass"
        ]
    ].copy()
)

print("\nV7.7 REGIME VERDICT")

if not survivors_v77.empty:

    frozen_regime_v77 = (
        survivors_v77
        .sort_values(
            [
                "val_ci_low",
                "val_accuracy",
            ],
            ascending=False
        )
        .iloc[0]
    )

    regime_verdict_v77 = (
        "FREEZE REGIME FOR HOLDOUT TEST"
    )

    print(
        f"Frozen regime: "
        f"{frozen_regime_v77['bucket']}"
    )

    print(
        f"Direction: "
        f"{frozen_regime_v77['direction']}"
    )

else:

    regime_verdict_v77 = (
        "NO REGIME SURVIVES VALIDATION"
    )

print(
    f"Verdict: "
    f"{regime_verdict_v77}"
)

print("REGIMES DISCOVERED USING TRAIN ONLY")
print("VALIDATION USED ONLY AFTER FREEZING")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

print("\nV7.8 FEATURE STABILITY AUDIT")

FEATURES_V78 = [
    "rsi14",
    "volume_ratio",
    "ema9",
    "ema21",
    "vwap",
    "minutes_et",
]

print(
    f"Core features to audit: "
    f"{len(FEATURES_V78)}"
)

for frame in [
    train3_purged,
    validation3_purged,
]:

    frame["ema_spread_v78"] = (
        (frame["ema9"] - frame["ema21"])
        / frame["close"]
    )

    frame["vwap_distance_v78"] = (
        (frame["close"] - frame["vwap"])
        / frame["close"]
    )

    frame["mom15_v78"] = (
        frame["close"]
        .pct_change(3)
        .shift(1)
    )

    frame["mom30_v78"] = (
        frame["close"]
        .pct_change(6)
        .shift(1)
    )

    frame["mom60_v78"] = (
        frame["close"]
        .pct_change(12)
        .shift(1)
    )

print("Derived stability features created")

AUDIT_FEATURES_V78 = [
    "rsi14",
    "volume_ratio",
    "ema_spread_v78",
    "vwap_distance_v78",
    "mom15_v78",
    "mom30_v78",
    "mom60_v78",
    "minutes_et",
]

print(
    "\nAUDIT FEATURES"
)

for feature in AUDIT_FEATURES_V78:
    print("-", feature)

def feature_corr_v78(
    frame,
    feature
):

    sample = frame[
        [feature, "future_return_60m"]
    ].replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    if len(sample) < 30:
        return {
            "rows": len(sample),
            "pearson": np.nan,
            "spearman": np.nan,
        }

    pearson = sample[
        feature
    ].corr(
        sample["future_return_60m"],
        method="pearson"
    )

    spearman = sample[
        feature
    ].corr(
        sample["future_return_60m"],
        method="spearman"
    )

    return {
        "rows": len(sample),
        "pearson": pearson,
        "spearman": spearman,
    }

print("Feature correlation helper ready")

feature_rows_v78 = []

for feature in AUDIT_FEATURES_V78:

    tr = feature_corr_v78(
        train3_purged,
        feature
    )

    va = feature_corr_v78(
        validation3_purged,
        feature
    )

    feature_rows_v78.append({
        "feature": feature,
        "train_rows": tr["rows"],
        "train_pearson": tr["pearson"],
        "train_spearman": tr["spearman"],
        "val_rows": va["rows"],
        "val_pearson": va["pearson"],
        "val_spearman": va["spearman"],
    })

feature_df_v78 = pd.DataFrame(
    feature_rows_v78
)

print("\nFEATURE CORRELATION TABLE")
print(feature_df_v78.to_string(index=False))

def same_sign(a, b):

    if pd.isna(a) or pd.isna(b):
        return False

    if a == 0 or b == 0:
        return False

    return np.sign(a) == np.sign(b)

feature_df_v78[
    "pearson_same_sign"
] = feature_df_v78.apply(
    lambda r: same_sign(
        r["train_pearson"],
        r["val_pearson"]
    ),
    axis=1
)

feature_df_v78[
    "spearman_same_sign"
] = feature_df_v78.apply(
    lambda r: same_sign(
        r["train_spearman"],
        r["val_spearman"]
    ),
    axis=1
)

print("Sign consistency calculated")

feature_df_v78[
    "min_abs_pearson"
] = feature_df_v78[
    [
        "train_pearson",
        "val_pearson",
    ]
].abs().min(axis=1)

feature_df_v78[
    "min_abs_spearman"
] = feature_df_v78[
    [
        "train_spearman",
        "val_spearman",
    ]
].abs().min(axis=1)

feature_df_v78[
    "stable_feature"
] = (
    feature_df_v78[
        "pearson_same_sign"
    ]
    & feature_df_v78[
        "spearman_same_sign"
    ]
    & (
        feature_df_v78[
            "min_abs_pearson"
        ] >= 0.02
    )
    & (
        feature_df_v78[
            "min_abs_spearman"
        ] >= 0.02
    )
)

print("\nV7.8 STABILITY GATE")

print(
    feature_df_v78[
        [
            "feature",
            "train_pearson",
            "val_pearson",
            "train_spearman",
            "val_spearman",
            "stable_feature",
        ]
    ].to_string(index=False)
)

stable_features_v78 = (
    feature_df_v78[
        feature_df_v78[
            "stable_feature"
        ]
    ].copy()
)

print("\nV7.8 FEATURE VERDICT")

if not stable_features_v78.empty:

    print(
        "STABLE FEATURES FOUND"
    )

    print(
        stable_features_v78[
            [
                "feature",
                "min_abs_pearson",
                "min_abs_spearman",
            ]
        ]
        .sort_values(
            [
                "min_abs_spearman",
                "min_abs_pearson",
            ],
            ascending=False
        )
        .to_string(index=False)
    )

    feature_verdict_v78 = (
        "BUILD NEXT STRATEGY ONLY FROM STABLE FEATURES"
    )

else:

    feature_verdict_v78 = (
        "NO CORE FEATURE SHOWS STABLE RELATIONSHIP"
    )

print(
    f"Verdict: "
    f"{feature_verdict_v78}"
)

print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

print("\nV7.9 TARGET-QUALITY AUDIT")

HORIZONS_V79 = {
    "15m": 3,
    "30m": 6,
    "60m": 12,
    "90m": 18,
    "120m": 24,
}

print("Auditing fixed horizons:", list(HORIZONS_V79.keys()))

def add_horizons_v79(frame):

    out = frame.copy()

    for label, bars in HORIZONS_V79.items():

        future_close = out["close"].shift(-bars)
        future_date = out["date_et"].shift(-bars)

        out[f"future_{label}"] = np.where(
            out["date_et"] == future_date,
            future_close / out["close"] - 1,
            np.nan
        )

    return out

train_v79 = add_horizons_v79(train3_purged)
validation_v79 = add_horizons_v79(validation3_purged)

print("Multi-horizon targets created")

target_rows_v79 = []

for label in HORIZONS_V79:

    col = f"future_{label}"

    for period, frame in [
        ("TRAIN", train_v79),
        ("VALIDATION", validation_v79),
    ]:

        x = frame[col].dropna()

        target_rows_v79.append({
            "horizon": label,
            "period": period,
            "rows": len(x),
            "up_rate": (x > 0).mean() * 100,
            "avg_return": x.mean() * 100,
            "median_return": x.median() * 100,
            "median_abs_move": x.abs().median() * 100,
        })

target_df_v79 = pd.DataFrame(target_rows_v79)

print("\nHORIZON TARGET SUMMARY")
print(target_df_v79.to_string(index=False))

print("\nMEANINGFUL-MOVE COVERAGE")

MOVE_LEVELS_V79 = [
    0.001,
    0.002,
    0.003,
]

move_rows_v79 = []

for label in HORIZONS_V79:

    col = f"future_{label}"

    for threshold in MOVE_LEVELS_V79:

        for period, frame in [
            ("TRAIN", train_v79),
            ("VALIDATION", validation_v79),
        ]:

            x = frame[col].dropna()

            meaningful = (
                x.abs() >= threshold
            )

            move_rows_v79.append({
                "horizon": label,
                "threshold_pct": threshold * 100,
                "period": period,
                "coverage_pct": meaningful.mean() * 100,
                "observations": int(meaningful.sum()),
            })

move_df_v79 = pd.DataFrame(move_rows_v79)

print(move_df_v79.to_string(index=False))

print("\nDIRECTION BALANCE CHECK")

balance_rows_v79 = []

for label in HORIZONS_V79:

    col = f"future_{label}"

    tr = train_v79[col].dropna()
    va = validation_v79[col].dropna()

    train_up = (tr > 0).mean() * 100
    val_up = (va > 0).mean() * 100

    balance_rows_v79.append({
        "horizon": label,
        "train_up_rate": train_up,
        "val_up_rate": val_up,
        "change": val_up - train_up,
    })

balance_df_v79 = pd.DataFrame(balance_rows_v79)

print(balance_df_v79.to_string(index=False))

print("\nMOVE-SIZE STABILITY CHECK")

size_rows_v79 = []

for label in HORIZONS_V79:

    col = f"future_{label}"

    tr = train_v79[col].dropna().abs()
    va = validation_v79[col].dropna().abs()

    size_rows_v79.append({
        "horizon": label,
        "train_median_abs_pct": tr.median() * 100,
        "val_median_abs_pct": va.median() * 100,
        "train_p75_abs_pct": tr.quantile(0.75) * 100,
        "val_p75_abs_pct": va.quantile(0.75) * 100,
    })

size_df_v79 = pd.DataFrame(size_rows_v79)

print(size_df_v79.to_string(index=False))

print("\nV7.9 NOISE DIAGNOSTIC")

audit_60 = target_df_v79[
    target_df_v79["horizon"] == "60m"
]

train_60 = audit_60[
    audit_60["period"] == "TRAIN"
].iloc[0]

val_60 = audit_60[
    audit_60["period"] == "VALIDATION"
].iloc[0]

sixty_stable = (
    abs(
        train_60["up_rate"]
        - val_60["up_rate"]
    ) <= 5
)

print(
    f"60m direction balance stable: "
    f"{sixty_stable}"
)

print(
    f"Train 60m median abs move: "
    f"{train_60['median_abs_move']:.4f}%"
)

print(
    f"Validation 60m median abs move: "
    f"{val_60['median_abs_move']:.4f}%"
)

print("\nV7.9 RESEARCH STATUS")

print("THIS IS TARGET DIAGNOSIS — NOT STRATEGY SELECTION")
print("NO HORIZON HAS BEEN PROMOTED")
print("NO THRESHOLD HAS BEEN TUNED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

target_df_v79.to_csv(
    "spy_sentinel_target_horizon_audit_v79.csv",
    index=False
)

move_df_v79.to_csv(
    "spy_sentinel_move_coverage_v79.csv",
    index=False
)

print("Target-quality audit saved")

print("\nV8.0 MEANINGFUL-MOVE TARGET")

MEANINGFUL_MOVE_V80 = 0.002

print(
    f"Frozen meaningful-move threshold: "
    f"{MEANINGFUL_MOVE_V80 * 100:.2f}%"
)

print(
    "Moves smaller than threshold "
    "are treated as NO-TRADE noise"
)

print("\nV8.0 MEANINGFUL-MOVE TARGET")

MEANINGFUL_MOVE_V80 = 0.002

print(
    f"Frozen meaningful-move threshold: "
    f"{MEANINGFUL_MOVE_V80 * 100:.2f}%"
)

print(
    "Moves smaller than threshold "
    "are treated as NO-TRADE noise"
)

def prepare_meaningful_v80(frame):

    data = frame.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna(
        subset=
        ML_FEATURES_V75
        + ["future_return_60m"]
    ).copy()

    data["meaningful_move_v80"] = (
        data["future_return_60m"].abs()
        >= MEANINGFUL_MOVE_V80
    )

    meaningful = data[
        data["meaningful_move_v80"]
    ].copy()

    meaningful["direction_target_v80"] = (
        meaningful["future_return_60m"] > 0
    ).astype(int)

    return data, meaningful

train_all_v80, train_move_v80 = (
    prepare_meaningful_v80(
        train3_purged
    )
)

val_all_v80, val_move_v80 = (
    prepare_meaningful_v80(
        validation3_purged
    )
)

print("Meaningful-move datasets created")

print("\nMEANINGFUL-MOVE COVERAGE")

for name, all_data, move_data in [
    (
        "TRAIN",
        train_all_v80,
        train_move_v80,
    ),
    (
        "VALIDATION",
        val_all_v80,
        val_move_v80,
    ),
]:

    coverage = (
        len(move_data)
        / len(all_data)
        * 100
        if len(all_data)
        else 0
    )

    up_rate = (
        move_data[
            "direction_target_v80"
        ].mean() * 100
        if len(move_data)
        else 0
    )

    print(
        f"{name}: "
        f"{len(move_data)} meaningful moves | "
        f"{coverage:.2f}% coverage | "
        f"{up_rate:.2f}% bullish"
    )

print("\nMEANINGFUL-MOVE TRAIN CV")

X_move_train_v80 = (
    train_move_v80[
        ML_FEATURES_V75
    ]
)

y_move_train_v80 = (
    train_move_v80[
        "direction_target_v80"
    ]
)

tscv_move_v80 = TimeSeriesSplit(
    n_splits=5
)

move_cv_rows_v80 = []

for fold, (tr_idx, te_idx) in enumerate(
    tscv_move_v80.split(
        X_move_train_v80
    ),
    start=1
):

    X_tr = X_move_train_v80.iloc[
        tr_idx
    ]

    X_te = X_move_train_v80.iloc[
        te_idx
    ]

    y_tr = y_move_train_v80.iloc[
        tr_idx
    ]

    y_te = y_move_train_v80.iloc[
        te_idx
    ]

    model = Pipeline([
        ("scale", StandardScaler()),
        (
            "logistic",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            )
        ),
    ])

    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)

    prob = model.predict_proba(
        X_te
    )[:, 1]

    bal = balanced_accuracy_score(
        y_te,
        pred
    ) * 100

    auc = roc_auc_score(
        y_te,
        prob
    ) * 100

    move_cv_rows_v80.append({
        "fold": fold,
        "balanced_accuracy": bal,
        "auc": auc,
    })

    print(
        f"Fold {fold}: "
        f"bal {bal:.2f}% | "
        f"AUC {auc:.2f}%"
    )

move_cv_df_v80 = pd.DataFrame(
    move_cv_rows_v80
)

move_cv_mean_bal_v80 = (
    move_cv_df_v80[
        "balanced_accuracy"
    ].mean()
)

move_cv_worst_bal_v80 = (
    move_cv_df_v80[
        "balanced_accuracy"
    ].min()
)

move_cv_mean_auc_v80 = (
    move_cv_df_v80[
        "auc"
    ].mean()
)

print("\nMEANINGFUL-MOVE CV STABILITY")

print(
    f"Mean balanced accuracy: "
    f"{move_cv_mean_bal_v80:.2f}%"
)

print(
    f"Worst balanced accuracy: "
    f"{move_cv_worst_bal_v80:.2f}%"
)

print(
    f"Mean AUC: "
    f"{move_cv_mean_auc_v80:.2f}%"
)

print("\nMEANINGFUL-MOVE VALIDATION")

move_model_v80 = Pipeline([
    ("scale", StandardScaler()),
    (
        "logistic",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )
    ),
])

move_model_v80.fit(
    train_move_v80[
        ML_FEATURES_V75
    ],
    train_move_v80[
        "direction_target_v80"
    ]
)

val_move_prob_v80 = (
    move_model_v80.predict_proba(
        val_move_v80[
            ML_FEATURES_V75
        ]
    )[:, 1]
)

val_move_pred_v80 = (
    val_move_prob_v80 >= 0.50
).astype(int)

val_move_bal_v80 = (
    balanced_accuracy_score(
        val_move_v80[
            "direction_target_v80"
        ],
        val_move_pred_v80
    ) * 100
)

val_move_auc_v80 = (
    roc_auc_score(
        val_move_v80[
            "direction_target_v80"
        ],
        val_move_prob_v80
    ) * 100
)

val_move_acc_v80 = (
    accuracy_score(
        val_move_v80[
            "direction_target_v80"
        ],
        val_move_pred_v80
    ) * 100
)

print(
    f"Validation accuracy: "
    f"{val_move_acc_v80:.2f}%"
)

print(
    f"Validation balanced accuracy: "
    f"{val_move_bal_v80:.2f}%"
)

print(
    f"Validation AUC: "
    f"{val_move_auc_v80:.2f}%"
)

print("\nMEANINGFUL-MOVE CONFIDENCE GATE")

confident_v80 = (
    (val_move_prob_v80 >= 0.60)
    | (val_move_prob_v80 <= 0.40)
)

conf_prob_v80 = (
    val_move_prob_v80[
        confident_v80
    ]
)

conf_actual_v80 = (
    val_move_v80[
        "direction_target_v80"
    ].to_numpy()[
        confident_v80
    ]
)

if len(conf_prob_v80):

    conf_pred_v80 = (
        conf_prob_v80 >= 0.50
    ).astype(int)

    conf_accuracy_v80 = (
        conf_pred_v80
        == conf_actual_v80
    ).mean() * 100

else:

    conf_accuracy_v80 = 0.0

conf_signals_v80 = len(
    conf_prob_v80
)

print(
    f"Confident signals: "
    f"{conf_signals_v80}"
)

print(
    f"Confident accuracy: "
    f"{conf_accuracy_v80:.2f}%"
)

print("\nV8.0 MEANINGFUL-MOVE GATE")

meaningful_candidate_v80 = (
    len(train_move_v80) >= 1000
    and len(val_move_v80) >= 300
    and move_cv_mean_bal_v80 >= 52
    and move_cv_worst_bal_v80 >= 48
    and move_cv_mean_auc_v80 >= 52
    and val_move_bal_v80 >= 52
    and val_move_auc_v80 >= 52
    and conf_signals_v80 >= 100
    and conf_accuracy_v80 >= 55
)

if meaningful_candidate_v80:

    meaningful_verdict_v80 = (
        "FREEZE MEANINGFUL-MOVE MODEL FOR HOLDOUT"
    )

else:

    meaningful_verdict_v80 = (
        "MEANINGFUL-MOVE MODEL NOT STRONG ENOUGH"
    )

print(
    f"Verdict: "
    f"{meaningful_verdict_v80}"
)

print("0.20% THRESHOLD WAS PREDEFINED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

move_cv_df_v80.to_csv(
    "spy_sentinel_meaningful_move_cv_v80.csv",
    index=False
)

print("Meaningful-move research saved")

print("\nV8.1 TWO-STAGE MOVE + DIRECTION MODEL")

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    roc_auc_score,
    accuracy_score,
)

MOVE_THRESHOLD_V81 = 0.002

print(
    f"Meaningful-move threshold: "
    f"{MOVE_THRESHOLD_V81 * 100:.2f}%"
)

FEATURES_V81 = [
    "rsi14",
    "volume_ratio",
    "ema_spread_v78",
    "vwap_distance_v78",
    "mom15_v78",
    "mom30_v78",
    "mom60_v78",
    "minutes_et",
]

def prepare_v81(frame):

    data = frame.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna(
        subset=FEATURES_V81
        + ["future_return_60m"]
    ).copy()

    data["meaningful_target"] = (
        data["future_return_60m"].abs()
        >= MOVE_THRESHOLD_V81
    ).astype(int)

    data["direction_target"] = (
        data["future_return_60m"] > 0
    ).astype(int)

    return data

train_v81 = prepare_v81(
    train3_purged
)

validation_v81 = prepare_v81(
    validation3_purged
)

print(f"Train rows: {len(train_v81)}")
print(f"Validation rows: {len(validation_v81)}")

print("\nSTAGE 1 — MEANINGFUL MOVE")

move_model_v81 = (
    HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=15,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=42,
    )
)

move_model_v81.fit(
    train_v81[FEATURES_V81],
    train_v81["meaningful_target"]
)

move_prob_v81 = (
    move_model_v81.predict_proba(
        validation_v81[FEATURES_V81]
    )[:, 1]
)

move_pred_v81 = (
    move_prob_v81 >= 0.50
).astype(int)

move_bal_v81 = (
    balanced_accuracy_score(
        validation_v81["meaningful_target"],
        move_pred_v81
    ) * 100
)

move_auc_v81 = (
    roc_auc_score(
        validation_v81["meaningful_target"],
        move_prob_v81
    ) * 100
)

print(
    f"Move balanced accuracy: "
    f"{move_bal_v81:.2f}%"
)

print(
    f"Move AUC: "
    f"{move_auc_v81:.2f}%"
)

print("\nSTAGE 2 — DIRECTION MODEL")

train_direction_v81 = train_v81[
    train_v81["meaningful_target"] == 1
].copy()

direction_model_v81 = (
    HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=42,
    )
)

direction_model_v81.fit(
    train_direction_v81[FEATURES_V81],
    train_direction_v81["direction_target"]
)

direction_prob_v81 = (
    direction_model_v81.predict_proba(
        validation_v81[FEATURES_V81]
    )[:, 1]
)

print(
    f"Meaningful training rows: "
    f"{len(train_direction_v81)}"
)

print("\nCOMBINED TWO-STAGE SIGNAL")

move_selected_v81 = (
    move_prob_v81 >= 0.55
)

direction_confident_v81 = (
    (direction_prob_v81 >= 0.55)
    | (direction_prob_v81 <= 0.45)
)

final_selected_v81 = (
    move_selected_v81
    & direction_confident_v81
)

selected_count_v81 = int(
    final_selected_v81.sum()
)

selected_direction_v81 = (
    direction_prob_v81[
        final_selected_v81
    ] >= 0.50
).astype(int)

actual_direction_v81 = (
    validation_v81[
        "direction_target"
    ].to_numpy()[
        final_selected_v81
    ]
)

if selected_count_v81:

    combined_accuracy_v81 = (
        selected_direction_v81
        == actual_direction_v81
    ).mean() * 100

else:

    combined_accuracy_v81 = 0.0

print(
    f"Combined signals: "
    f"{selected_count_v81}"
)

print(
    f"Combined direction accuracy: "
    f"{combined_accuracy_v81:.2f}%"
)

selected_returns_v81 = (
    validation_v81[
        "future_return_60m"
    ].to_numpy()[
        final_selected_v81
    ]
)

if selected_count_v81:

    signed_returns_v81 = np.where(
        selected_direction_v81 == 1,
        selected_returns_v81,
        -selected_returns_v81
    )

    avg_directional_return_v81 = (
        np.mean(signed_returns_v81)
        * 100
    )

    median_directional_return_v81 = (
        np.median(signed_returns_v81)
        * 100
    )

else:

    avg_directional_return_v81 = 0.0
    median_directional_return_v81 = 0.0

print("\nTWO-STAGE RETURN QUALITY")

print(
    f"Average directional return: "
    f"{avg_directional_return_v81:+.4f}%"
)

print(
    f"Median directional return: "
    f"{median_directional_return_v81:+.4f}%"
)

combined_ci_low_v81 = (
    wilson_low_v72(
        combined_accuracy_v81,
        selected_count_v81
    )
    if selected_count_v81
    else 0.0
)

print(
    f"Combined 95% CI low: "
    f"{combined_ci_low_v81:.2f}%"
)

two_stage_pass_v81 = (
    move_bal_v81 >= 52
    and move_auc_v81 >= 52
    and selected_count_v81 >= 150
    and combined_accuracy_v81 >= 55
    and combined_ci_low_v81 > 50
    and avg_directional_return_v81 > 0
)

print("\nV8.1 TWO-STAGE GATE")

if two_stage_pass_v81:
    verdict_v81 = (
        "FREEZE TWO-STAGE MODEL FOR HOLDOUT"
    )
else:
    verdict_v81 = (
        "TWO-STAGE MODEL NOT STRONG ENOUGH"
    )

print(f"Verdict: {verdict_v81}")
print("MOVE THRESHOLD WAS PREDEFINED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "move_balanced_accuracy": move_bal_v81,
    "move_auc": move_auc_v81,
    "combined_signals": selected_count_v81,
    "combined_accuracy": combined_accuracy_v81,
    "combined_ci_low": combined_ci_low_v81,
    "avg_directional_return": avg_directional_return_v81,
    "passed": two_stage_pass_v81,
    "verdict": verdict_v81,
}]).to_csv(
    "spy_sentinel_two_stage_v81.csv",
    index=False
)

print("Two-stage research saved")

print("\nV8.3 CROSS-MARKET FEATURE ENGINE")

from pathlib import Path

CROSS_BASE = (
    Path.home()
    / "Documents"
    / "ai trading bot"
)

CROSS_SYMBOLS = [
    "QQQ",
    "XLK",
    "XLF",
]

print(
    "Cross-market symbols:",
    CROSS_SYMBOLS
)

def load_cross_symbol_v83(symbol):

    f = (
        CROSS_BASE
        / f"{symbol}_5min_3years_clean.csv"
    )

    df = pd.read_csv(f)

    tcol = next(
        c for c in df.columns
        if "time" in c.lower()
        or "date" in c.lower()
    )

    df["timestamp_utc"] = pd.to_datetime(
        df[tcol],
        utc=True
    )

    df = df.sort_values(
        "timestamp_utc"
    ).copy()

    df["time_et_cross"] = (
        df["timestamp_utc"]
        .dt.tz_convert(
            "America/New_York"
        )
    )

    df["date_et_cross"] = (
        df["time_et_cross"].dt.date
    )

    return df

print("Cross-market loader ready")

cross_frames_v83 = {}

for symbol in CROSS_SYMBOLS:

    frame = load_cross_symbol_v83(
        symbol
    )

    frame[
        f"{symbol.lower()}_ret15_lag"
    ] = (
        frame.groupby(
            "date_et_cross"
        )["close"]
        .pct_change(3)
        .shift(1)
    )

    frame[
        f"{symbol.lower()}_ret30_lag"
    ] = (
        frame.groupby(
            "date_et_cross"
        )["close"]
        .pct_change(6)
        .shift(1)
    )

    cross_frames_v83[symbol] = frame

    print(
        symbol,
        "rows:",
        len(frame)
    )

cross_merged_v83 = clean3[
    [
        "timestamp_utc",
        "date_et",
        "close",
        "future_return_60m",
    ]
].copy()

for symbol in CROSS_SYMBOLS:

    frame = cross_frames_v83[
        symbol
    ]

    keep = [
        "timestamp_utc",
        f"{symbol.lower()}_ret15_lag",
        f"{symbol.lower()}_ret30_lag",
    ]

    cross_merged_v83 = (
        cross_merged_v83.merge(
            frame[keep],
            on="timestamp_utc",
            how="left",
            validate="one_to_one",
        )
    )

print(
    "Merged rows:",
    len(cross_merged_v83)
)

print(
    "Cross-market merge complete"
)

cross_merged_v83[
    "spy_ret15_lag"
] = (
    clean3.groupby("date_et")[
        "close"
    ]
    .pct_change(3)
    .shift(1)
    .to_numpy()
)

cross_merged_v83[
    "spy_ret30_lag"
] = (
    clean3.groupby("date_et")[
        "close"
    ]
    .pct_change(6)
    .shift(1)
    .to_numpy()
)

for symbol in CROSS_SYMBOLS:

    s = symbol.lower()

    cross_merged_v83[
        f"{s}_relative15"
    ] = (
        cross_merged_v83[
            f"{s}_ret15_lag"
        ]
        - cross_merged_v83[
            "spy_ret15_lag"
        ]
    )

    cross_merged_v83[
        f"{s}_relative30"
    ] = (
        cross_merged_v83[
            f"{s}_ret30_lag"
        ]
        - cross_merged_v83[
            "spy_ret30_lag"
        ]
    )

print("Relative-strength features built")

CROSS_FEATURES_V83 = [
    "qqq_ret15_lag",
    "qqq_ret30_lag",
    "xlk_ret15_lag",
    "xlk_ret30_lag",
    "xlf_ret15_lag",
    "xlf_ret30_lag",
    "qqq_relative15",
    "qqq_relative30",
    "xlk_relative15",
    "xlk_relative30",
    "xlf_relative15",
    "xlf_relative30",
]

train_cross_v83 = (
    cross_merged_v83[
        cross_merged_v83[
            "date_et"
        ].isin(train_days)
    ]
    .iloc[:-12]
    .copy()
)

validation_cross_v83 = (
    cross_merged_v83[
        cross_merged_v83[
            "date_et"
        ].isin(validation_days)
    ]
    .iloc[:-12]
    .copy()
)

print(
    "Train cross rows:",
    len(train_cross_v83)
)

print(
    "Validation cross rows:",
    len(validation_cross_v83)
)

cross_rows_v83 = []

for feature in CROSS_FEATURES_V83:

    tr = feature_corr_v78(
        train_cross_v83,
        feature
    )

    va = feature_corr_v78(
        validation_cross_v83,
        feature
    )

    cross_rows_v83.append({
        "feature": feature,
        "train_pearson": tr["pearson"],
        "train_spearman": tr["spearman"],
        "val_pearson": va["pearson"],
        "val_spearman": va["spearman"],
    })

cross_df_v83 = pd.DataFrame(
    cross_rows_v83
)

print("\nCROSS-MARKET CORRELATIONS")

print(
    cross_df_v83.to_string(
        index=False
    )
)

cross_df_v83[
    "pearson_same_sign"
] = cross_df_v83.apply(
    lambda r: same_sign(
        r["train_pearson"],
        r["val_pearson"]
    ),
    axis=1
)

cross_df_v83[
    "spearman_same_sign"
] = cross_df_v83.apply(
    lambda r: same_sign(
        r["train_spearman"],
        r["val_spearman"]
    ),
    axis=1
)

cross_df_v83[
    "stable_cross_feature"
] = (
    cross_df_v83[
        "pearson_same_sign"
    ]
    & cross_df_v83[
        "spearman_same_sign"
    ]
    & (
        cross_df_v83[
            ["train_pearson", "val_pearson"]
        ]
        .abs()
        .min(axis=1)
        >= 0.02
    )
    & (
        cross_df_v83[
            ["train_spearman", "val_spearman"]
        ]
        .abs()
        .min(axis=1)
        >= 0.02
    )
)

print("\nV8.3 CROSS-MARKET STABILITY GATE")

print(
    cross_df_v83[
        [
            "feature",
            "train_pearson",
            "val_pearson",
            "train_spearman",
            "val_spearman",
            "stable_cross_feature",
        ]
    ].to_string(index=False)
)

print("\nHOLDOUT PERFORMANCE REMAINS SEALED")
print("NO CROSS-MARKET STRATEGY TESTED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

print("\nV8.4 CROSS-MARKET BREADTH TEST")

for frame in [
    train_cross_v83,
    validation_cross_v83,
]:

    frame["cross_positive_count"] = (
        (frame["qqq_ret30_lag"] > 0).astype(int)
        + (frame["xlk_ret30_lag"] > 0).astype(int)
        + (frame["xlf_ret30_lag"] > 0).astype(int)
    )

    frame["cross_negative_count"] = (
        (frame["qqq_ret30_lag"] < 0).astype(int)
        + (frame["xlk_ret30_lag"] < 0).astype(int)
        + (frame["xlf_ret30_lag"] < 0).astype(int)
    )

print("Cross-market breadth counts created")

BREADTH_RULES_V84 = [
    "UNANIMOUS_3_OF_3",
    "MAJORITY_2_OF_3",
]

def build_breadth_signal_v84(frame, rule):

    sample = frame.copy()

    sample["breadth_signal"] = "NO TRADE"

    if rule == "UNANIMOUS_3_OF_3":

        sample.loc[
            sample["cross_positive_count"] == 3,
            "breadth_signal"
        ] = "BULLISH"

        sample.loc[
            sample["cross_negative_count"] == 3,
            "breadth_signal"
        ] = "BEARISH"

    elif rule == "MAJORITY_2_OF_3":

        sample.loc[
            sample["cross_positive_count"] >= 2,
            "breadth_signal"
        ] = "BULLISH"

        sample.loc[
            sample["cross_negative_count"] >= 2,
            "breadth_signal"
        ] = "BEARISH"

    return sample

breadth_rows_v84 = []

for rule in BREADTH_RULES_V84:

    tr_frame = build_breadth_signal_v84(
        train_cross_v83,
        rule
    )

    va_frame = build_breadth_signal_v84(
        validation_cross_v83,
        rule
    )

    tr = evaluate_signal_v72(
        tr_frame,
        "breadth_signal"
    )

    va = evaluate_signal_v72(
        va_frame,
        "breadth_signal"
    )

    breadth_rows_v84.append({
        "rule": rule,
        "train_signals": tr["signals"],
        "train_accuracy": tr["accuracy"],
        "train_avg_return": tr["avg_return"],
        "val_signals": va["signals"],
        "val_accuracy": va["accuracy"],
        "val_avg_return": va["avg_return"],
        "accuracy_gap": abs(
            tr["accuracy"] - va["accuracy"]
        ),
    })

breadth_df_v84 = pd.DataFrame(
    breadth_rows_v84
)

print("\nCROSS-MARKET BREADTH RESULTS")
print(breadth_df_v84.to_string(index=False))

breadth_df_v84["val_ci_low"] = (
    breadth_df_v84.apply(
        lambda r: wilson_low_v72(
            r["val_accuracy"],
            int(r["val_signals"])
        ),
        axis=1
    )
)

print("\nBREADTH CONFIDENCE CHECK")

print(
    breadth_df_v84[
        [
            "rule",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "val_avg_return",
        ]
    ].to_string(index=False)
)

breadth_df_v84["strict_pass"] = (
    (breadth_df_v84["train_signals"] >= 300)
    & (breadth_df_v84["val_signals"] >= 100)
    & (breadth_df_v84["train_accuracy"] >= 53)
    & (breadth_df_v84["val_accuracy"] >= 55)
    & (breadth_df_v84["train_avg_return"] > 0)
    & (breadth_df_v84["val_avg_return"] > 0)
    & (breadth_df_v84["accuracy_gap"] <= 8)
    & (breadth_df_v84["val_ci_low"] > 50)
)

print("\nV8.4 STRICT BREADTH GATE")

print(
    breadth_df_v84[
        [
            "rule",
            "train_accuracy",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "strict_pass",
        ]
    ].to_string(index=False)
)

breadth_df_v84["strict_pass"] = (
    (breadth_df_v84["train_signals"] >= 300)
    & (breadth_df_v84["val_signals"] >= 100)
    & (breadth_df_v84["train_accuracy"] >= 53)
    & (breadth_df_v84["val_accuracy"] >= 55)
    & (breadth_df_v84["train_avg_return"] > 0)
    & (breadth_df_v84["val_avg_return"] > 0)
    & (breadth_df_v84["accuracy_gap"] <= 8)
    & (breadth_df_v84["val_ci_low"] > 50)
)

print("\nV8.4 STRICT BREADTH GATE")

print(
    breadth_df_v84[
        [
            "rule",
            "train_accuracy",
            "val_accuracy",
            "val_ci_low",
            "val_signals",
            "strict_pass",
        ]
    ].to_string(index=False)
)

breadth_eligible_v84 = (
    breadth_df_v84[
        breadth_df_v84["strict_pass"]
    ].copy()
)

print("\nV8.4 CANDIDATE SELECTION")

if not breadth_eligible_v84.empty:

    winner_v84 = (
        breadth_eligible_v84
        .sort_values(
            [
                "val_ci_low",
                "val_accuracy",
                "val_signals",
            ],
            ascending=False
        )
        .iloc[0]
    )

    frozen_breadth_v84 = winner_v84["rule"]

    verdict_v84 = (
        "FREEZE BREADTH RULE FOR HOLDOUT"
    )

    print(
        f"Frozen candidate: "
        f"{frozen_breadth_v84}"
    )

else:

    frozen_breadth_v84 = "NONE"

    verdict_v84 = (
        "NO BREADTH RULE SURVIVES"
    )

print(f"Verdict: {verdict_v84}")

print("\nRESEARCH SAFETY STATUS")
print("ONLY TWO PREDEFINED BREADTH RULES TESTED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("NO HOLDOUT TUNING")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

breadth_df_v84.to_csv(
    "spy_sentinel_cross_market_breadth_v84.csv",
    index=False
)

pd.DataFrame([{
    "frozen_rule": frozen_breadth_v84,
    "verdict": verdict_v84,
}]).to_csv(
    "spy_sentinel_cross_market_breadth_candidate_v84.csv",
    index=False
)

print("Cross-market breadth research saved")

print("\nV8.5 CROSS-MARKET ML MODEL")

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    roc_auc_score,
    accuracy_score,
)

print("Cross-market ML libraries ready")

CROSS_ML_FEATURES_V85 = [
    "qqq_ret15_lag",
    "qqq_ret30_lag",
    "xlk_ret15_lag",
    "xlk_ret30_lag",
    "xlf_ret15_lag",
    "xlf_ret30_lag",
    "qqq_relative15",
    "qqq_relative30",
    "xlk_relative15",
    "xlk_relative30",
    "xlf_relative15",
    "xlf_relative30",
    "spy_ret15_lag",
    "spy_ret30_lag",
]

def prepare_cross_ml_v85(frame):

    data = frame.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna(
        subset=CROSS_ML_FEATURES_V85
        + ["future_return_60m"]
    ).copy()

    data["target_v85"] = (
        data["future_return_60m"] > 0
    ).astype(int)

    return data

cross_train_ml_v85 = prepare_cross_ml_v85(
    train_cross_v83
)

cross_val_ml_v85 = prepare_cross_ml_v85(
    validation_cross_v83
)

print(
    f"Cross train rows: "
    f"{len(cross_train_ml_v85)}"
)

print(
    f"Cross validation rows: "
    f"{len(cross_val_ml_v85)}"
)

print("\nCROSS-MARKET TRAIN CV")

X_cross_v85 = cross_train_ml_v85[
    CROSS_ML_FEATURES_V85
]

y_cross_v85 = cross_train_ml_v85[
    "target_v85"
]

cross_cv_rows_v85 = []

for fold, (tr_idx, te_idx) in enumerate(
    tscv_v75.split(X_cross_v85),
    start=1
):

    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=15,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=42,
    )

    X_tr = X_cross_v85.iloc[tr_idx]
    X_te = X_cross_v85.iloc[te_idx]

    y_tr = y_cross_v85.iloc[tr_idx]
    y_te = y_cross_v85.iloc[te_idx]

    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)
    prob = model.predict_proba(X_te)[:, 1]

    bal = (
        balanced_accuracy_score(
            y_te,
            pred
        ) * 100
    )

    auc = (
        roc_auc_score(
            y_te,
            prob
        ) * 100
    )

    cross_cv_rows_v85.append({
        "fold": fold,
        "balanced_accuracy": bal,
        "auc": auc,
    })

    print(
        f"Fold {fold}: "
        f"bal {bal:.2f}% | "
        f"AUC {auc:.2f}%"
    )

cross_cv_df_v85 = pd.DataFrame(
    cross_cv_rows_v85
)

cross_cv_mean_bal_v85 = (
    cross_cv_df_v85[
        "balanced_accuracy"
    ].mean()
)

cross_cv_worst_bal_v85 = (
    cross_cv_df_v85[
        "balanced_accuracy"
    ].min()
)

cross_cv_mean_auc_v85 = (
    cross_cv_df_v85["auc"].mean()
)

print("\nCROSS-MARKET CV STABILITY")

print(
    f"Mean balanced accuracy: "
    f"{cross_cv_mean_bal_v85:.2f}%"
)

print(
    f"Worst balanced accuracy: "
    f"{cross_cv_worst_bal_v85:.2f}%"
)

print(
    f"Mean AUC: "
    f"{cross_cv_mean_auc_v85:.2f}%"
)

print("\nCROSS-MARKET VALIDATION")

cross_model_v85 = HistGradientBoostingClassifier(
    learning_rate=0.05,
    max_iter=200,
    max_leaf_nodes=15,
    min_samples_leaf=40,
    l2_regularization=1.0,
    random_state=42,
)

cross_model_v85.fit(
    cross_train_ml_v85[
        CROSS_ML_FEATURES_V85
    ],
    cross_train_ml_v85[
        "target_v85"
    ]
)

cross_val_prob_v85 = (
    cross_model_v85.predict_proba(
        cross_val_ml_v85[
            CROSS_ML_FEATURES_V85
        ]
    )[:, 1]
)

cross_val_pred_v85 = (
    cross_val_prob_v85 >= 0.50
).astype(int)

cross_val_bal_v85 = (
    balanced_accuracy_score(
        cross_val_ml_v85["target_v85"],
        cross_val_pred_v85
    ) * 100
)

cross_val_auc_v85 = (
    roc_auc_score(
        cross_val_ml_v85["target_v85"],
        cross_val_prob_v85
    ) * 100
)

print(
    f"Validation balanced accuracy: "
    f"{cross_val_bal_v85:.2f}%"
)

print(
    f"Validation AUC: "
    f"{cross_val_auc_v85:.2f}%"
)

print("\nCROSS-MARKET HIGH-CONFIDENCE TEST")

cross_selected_v85 = (
    (cross_val_prob_v85 >= 0.55)
    | (cross_val_prob_v85 <= 0.45)
)

cross_selected_probs_v85 = (
    cross_val_prob_v85[
        cross_selected_v85
    ]
)

cross_selected_actual_v85 = (
    cross_val_ml_v85[
        "target_v85"
    ].to_numpy()[
        cross_selected_v85
    ]
)

if len(cross_selected_probs_v85):

    cross_selected_pred_v85 = (
        cross_selected_probs_v85
        >= 0.50
    ).astype(int)

    cross_hc_accuracy_v85 = (
        cross_selected_pred_v85
        == cross_selected_actual_v85
    ).mean() * 100

else:

    cross_hc_accuracy_v85 = 0.0

cross_hc_signals_v85 = len(
    cross_selected_probs_v85
)

print(
    f"High-confidence signals: "
    f"{cross_hc_signals_v85}"
)

print(
    f"High-confidence accuracy: "
    f"{cross_hc_accuracy_v85:.2f}%"
)

cross_ci_low_v85 = (
    wilson_low_v72(
        cross_hc_accuracy_v85,
        cross_hc_signals_v85
    )
    if cross_hc_signals_v85
    else 0.0
)

print(
    f"High-confidence 95% CI low: "
    f"{cross_ci_low_v85:.2f}%"
)

cross_ml_pass_v85 = (
    cross_cv_mean_bal_v85 >= 52
    and cross_cv_worst_bal_v85 >= 48
    and cross_cv_mean_auc_v85 >= 52
    and cross_val_bal_v85 >= 52
    and cross_val_auc_v85 >= 52
    and cross_hc_signals_v85 >= 150
    and cross_hc_accuracy_v85 >= 55
    and cross_ci_low_v85 > 50
)

cross_ci_low_v85 = (
    wilson_low_v72(
        cross_hc_accuracy_v85,
        cross_hc_signals_v85
    )
    if cross_hc_signals_v85
    else 0.0
)

print(
    f"High-confidence 95% CI low: "
    f"{cross_ci_low_v85:.2f}%"
)

cross_ml_pass_v85 = (
    cross_cv_mean_bal_v85 >= 52
    and cross_cv_worst_bal_v85 >= 48
    and cross_cv_mean_auc_v85 >= 52
    and cross_val_bal_v85 >= 52
    and cross_val_auc_v85 >= 52
    and cross_hc_signals_v85 >= 150
    and cross_hc_accuracy_v85 >= 55
    and cross_ci_low_v85 > 50
)

print("\nV8.5 CROSS-MARKET ML GATE")

if cross_ml_pass_v85:
    cross_ml_verdict_v85 = (
        "FREEZE CROSS-MARKET ML MODEL FOR HOLDOUT"
    )
else:
    cross_ml_verdict_v85 = (
        "CROSS-MARKET ML MODEL NOT STRONG ENOUGH"
    )

print(
    f"Verdict: "
    f"{cross_ml_verdict_v85}"
)

print("TRAIN CV + SEPARATE VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("NO HOLDOUT TRAINING OR TUNING")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

cross_cv_df_v85.to_csv(
    "spy_sentinel_cross_market_ml_cv_v85.csv",
    index=False
)

pd.DataFrame([{
    "cv_mean_bal": cross_cv_mean_bal_v85,
    "cv_worst_bal": cross_cv_worst_bal_v85,
    "cv_mean_auc": cross_cv_mean_auc_v85,
    "val_bal": cross_val_bal_v85,
    "val_auc": cross_val_auc_v85,
    "hc_signals": cross_hc_signals_v85,
    "hc_accuracy": cross_hc_accuracy_v85,
    "hc_ci_low": cross_ci_low_v85,
    "passed": cross_ml_pass_v85,
    "verdict": cross_ml_verdict_v85,
}]).to_csv(
    "spy_sentinel_cross_market_ml_v85.csv",
    index=False
)

print("Cross-market ML research saved")

print("\nV8.6 TRUE 3-YEAR OPENING RANGE BREAKOUT")

def add_opening_range_v86(frame):

    out = frame.copy()

    opening = out[
        (out["minutes_et"] >= 570)
        & (out["minutes_et"] < 600)
    ].copy()

    daily = (
        opening.groupby("date_et")
        .agg(
            opening_high=("high", "max"),
            opening_low=("low", "min"),
        )
    )

    out["opening_high_v86"] = (
        out["date_et"].map(
            daily["opening_high"]
        )
    )

    out["opening_low_v86"] = (
        out["date_et"].map(
            daily["opening_low"]
        )
    )

    return out

train_orb_v86 = add_opening_range_v86(
    train3_purged
)

validation_orb_v86 = add_opening_range_v86(
    validation3_purged
)

print("Opening ranges created")

def first_breakout_v86(frame):

    candidates = frame[
        (frame["minutes_et"] >= 600)
        & (frame["minutes_et"] < 900)
    ].copy()

    candidates["orb_signal_v86"] = "NO TRADE"

    candidates.loc[
        candidates["close"]
        > candidates["opening_high_v86"],
        "orb_signal_v86"
    ] = "BULLISH"

    candidates.loc[
        candidates["close"]
        < candidates["opening_low_v86"],
        "orb_signal_v86"
    ] = "BEARISH"

    signals = candidates[
        candidates["orb_signal_v86"].isin(
            ["BULLISH", "BEARISH"]
        )
    ].copy()

    first_each_day = (
        signals
        .sort_values("time_et")
        .groupby("date_et", as_index=False)
        .first()
    )

    return first_each_day

train_orb_signals_v86 = (
    first_breakout_v86(
        train_orb_v86
    )
)

validation_orb_signals_v86 = (
    first_breakout_v86(
        validation_orb_v86
    )
)

print(
    "Train breakout days:",
    len(train_orb_signals_v86)
)

print(
    "Validation breakout days:",
    len(validation_orb_signals_v86)
)

train_orb_stats_v86 = evaluate_signal_v72(
    train_orb_signals_v86,
    "orb_signal_v86"
)

validation_orb_stats_v86 = evaluate_signal_v72(
    validation_orb_signals_v86,
    "orb_signal_v86"
)

print("\nOPENING RANGE BREAKOUT RESULTS")

print(
    f"TRAIN: "
    f"{train_orb_stats_v86['accuracy']:.2f}% | "
    f"{train_orb_stats_v86['signals']} signals | "
    f"avg {train_orb_stats_v86['avg_return']:+.4f}%"
)

print(
    f"VALIDATION: "
    f"{validation_orb_stats_v86['accuracy']:.2f}% | "
    f"{validation_orb_stats_v86['signals']} signals | "
    f"avg {validation_orb_stats_v86['avg_return']:+.4f}%"
)

orb_ci_low_v86 = wilson_low_v72(
    validation_orb_stats_v86[
        "accuracy"
    ],
    validation_orb_stats_v86[
        "signals"
    ]
)

print(
    f"Validation 95% CI low: "
    f"{orb_ci_low_v86:.2f}%"
)

orb_accuracy_gap_v86 = abs(
    train_orb_stats_v86["accuracy"]
    - validation_orb_stats_v86["accuracy"]
)

print(
    f"Train/validation accuracy gap: "
    f"{orb_accuracy_gap_v86:.2f}%"
)

orb_pass_v86 = (
    train_orb_stats_v86["signals"] >= 250
    and validation_orb_stats_v86["signals"] >= 80
    and train_orb_stats_v86["accuracy"] >= 53
    and validation_orb_stats_v86["accuracy"] >= 55
    and train_orb_stats_v86["avg_return"] > 0
    and validation_orb_stats_v86["avg_return"] > 0
    and orb_accuracy_gap_v86 <= 8
    and orb_ci_low_v86 > 50
)

print("\nV8.6 ORB STRICT GATE")

print(
    f"Opening-range breakout passes: "
    f"{orb_pass_v86}"
)

print("\nV8.6 ORB VERDICT")

if orb_pass_v86:
    orb_verdict_v86 = (
        "FREEZE OPENING-RANGE BREAKOUT FOR HOLDOUT"
    )
else:
    orb_verdict_v86 = (
        "OPENING-RANGE BREAKOUT NOT STRONG ENOUGH"
    )

print(f"Verdict: {orb_verdict_v86}")

print("\nRESEARCH SAFETY STATUS")
print("OPENING RANGE FIXED AT 9:30-10:00 ET")
print("ONLY FIRST BREAKOUT PER DAY USED")
print("NO BREAKOUT BUFFER WAS OPTIMIZED")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "train_signals": train_orb_stats_v86["signals"],
    "train_accuracy": train_orb_stats_v86["accuracy"],
    "train_avg_return": train_orb_stats_v86["avg_return"],
    "val_signals": validation_orb_stats_v86["signals"],
    "val_accuracy": validation_orb_stats_v86["accuracy"],
    "val_avg_return": validation_orb_stats_v86["avg_return"],
    "val_ci_low": orb_ci_low_v86,
    "accuracy_gap": orb_accuracy_gap_v86,
    "passed": orb_pass_v86,
    "verdict": orb_verdict_v86,
}]).to_csv(
    "spy_sentinel_true3year_orb_v86.csv",
    index=False
)

print("Opening-range breakout research saved")

print("\nV8.7 TIME-OF-DAY + VOLATILITY DIAGNOSTIC")

for frame in [
    train3_purged,
    validation3_purged,
]:

    high_low = (
        frame["high"] - frame["low"]
    )

    high_close = (
        frame["high"]
        - frame["close"].shift(1)
    ).abs()

    low_close = (
        frame["low"]
        - frame["close"].shift(1)
    ).abs()

    frame["tr_v87"] = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    frame["atr14_v87"] = (
        frame["tr_v87"]
        .rolling(14)
        .mean()
        .shift(1)
    )

    frame["atr_pct_v87"] = (
        frame["atr14_v87"]
        / frame["close"]
    )

print("Lagged ATR features created")

train_q1_v87 = (
    train3_purged[
        "atr_pct_v87"
    ].quantile(0.25)
)

train_q2_v87 = (
    train3_purged[
        "atr_pct_v87"
    ].quantile(0.50)
)

train_q3_v87 = (
    train3_purged[
        "atr_pct_v87"
    ].quantile(0.75)
)

print("\nTRAIN-FROZEN VOLATILITY CUTS")
print(f"Q1: {train_q1_v87:.6f}")
print(f"Q2: {train_q2_v87:.6f}")
print(f"Q3: {train_q3_v87:.6f}")

def label_context_v87(frame):

    out = frame.copy()

    out["session_v87"] = np.select(
        [
            out["minutes_et"] < 660,
            out["minutes_et"] < 810,
        ],
        [
            "MORNING",
            "MIDDAY",
        ],
        default="AFTERNOON",
    )

    out["vol_bucket_v87"] = np.select(
        [
            out["atr_pct_v87"] < train_q1_v87,
            out["atr_pct_v87"] < train_q2_v87,
            out["atr_pct_v87"] < train_q3_v87,
        ],
        [
            "VOL_Q1",
            "VOL_Q2",
            "VOL_Q3",
        ],
        default="VOL_Q4",
    )

    out["context_v87"] = (
        out["session_v87"]
        + "|"
        + out["vol_bucket_v87"]
    )

    return out

train_context_v87 = label_context_v87(
    train3_purged
)

validation_context_v87 = label_context_v87(
    validation3_purged
)

print("Context labels created")

def context_summary_v87(frame):

    usable = frame.dropna(
        subset=[
            "future_return_60m",
            "context_v87",
        ]
    ).copy()

    summary = (
        usable
        .groupby("context_v87")
        .agg(
            observations=(
                "future_return_60m",
                "size"
            ),
            up_rate=(
                "future_return_60m",
                lambda x: (
                    (x > 0).mean() * 100
                )
            ),
            avg_return=(
                "future_return_60m",
                lambda x: (
                    x.mean() * 100
                )
            ),
            median_return=(
                "future_return_60m",
                lambda x: (
                    x.median() * 100
                )
            ),
        )
        .reset_index()
    )

    return summary

train_context_summary_v87 = (
    context_summary_v87(
        train_context_v87
    )
)

validation_context_summary_v87 = (
    context_summary_v87(
        validation_context_v87
    )
)

print("\nTRAIN CONTEXT SUMMARY")
print(
    train_context_summary_v87.to_string(
        index=False
    )
)

print("\nVALIDATION CONTEXT SUMMARY")

print(
    validation_context_summary_v87.to_string(
        index=False
    )
)

context_compare_v87 = (
    train_context_summary_v87.merge(
        validation_context_summary_v87,
        on="context_v87",
        suffixes=(
            "_train",
            "_val"
        ),
        how="inner",
    )
)

context_compare_v87[
    "train_edge"
] = abs(
    context_compare_v87[
        "up_rate_train"
    ] - 50
)

context_compare_v87[
    "val_edge"
] = abs(
    context_compare_v87[
        "up_rate_val"
    ] - 50
)

context_compare_v87[
    "same_direction"
] = (
    (
        context_compare_v87[
            "up_rate_train"
        ] >= 50
    )
    ==
    (
        context_compare_v87[
            "up_rate_val"
        ] >= 50
    )
)

print("\nTRAIN VS VALIDATION CONTEXT")
print(
    context_compare_v87.to_string(
        index=False
    )
)

context_compare_v87[
    "diagnostic_stable"
] = (
    (
        context_compare_v87[
            "observations_train"
        ] >= 500
    )
    & (
        context_compare_v87[
            "observations_val"
        ] >= 150
    )
    & (
        context_compare_v87[
            "train_edge"
        ] >= 3
    )
    & (
        context_compare_v87[
            "val_edge"
        ] >= 3
    )
    & context_compare_v87[
        "same_direction"
    ]
)

print("\nV8.7 STABILITY SCREEN")

print(
    context_compare_v87[
        [
            "context_v87",
            "observations_train",
            "up_rate_train",
            "observations_val",
            "up_rate_val",
            "train_edge",
            "val_edge",
            "same_direction",
            "diagnostic_stable",
        ]
    ].to_string(index=False)
)

stable_contexts_v87 = (
    context_compare_v87[
        context_compare_v87[
            "diagnostic_stable"
        ]
    ].copy()
)

print("\nV8.7 DIAGNOSTIC VERDICT")

if stable_contexts_v87.empty:

    verdict_v87 = (
        "NO TIME-VOL CONTEXT SHOWS STABLE BIAS"
    )

else:

    verdict_v87 = (
        "STABLE TIME-VOL CONTEXTS FOUND"
    )

    print(
        stable_contexts_v87[
            [
                "context_v87",
                "up_rate_train",
                "up_rate_val",
                "avg_return_train",
                "avg_return_val",
            ]
        ].to_string(index=False)
    )

print(f"Verdict: {verdict_v87}")
print("THIS IS DIAGNOSIS, NOT A TRADING RULE")
print("VOLATILITY CUTS FROZEN FROM TRAIN ONLY")
print("TRAIN + VALIDATION ONLY")
print("HOLDOUT PERFORMANCE REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

context_compare_v87.to_csv(
    "spy_sentinel_time_vol_diagnostic_v87.csv",
    index=False
)

print("Time-volatility diagnostic saved")

print("\nV8.8 FROZEN TIME-VOL ROBUSTNESS TEST")

FROZEN_CONTEXTS_V88 = [
    "MIDDAY|VOL_Q2",
    "MIDDAY|VOL_Q3",
    "AFTERNOON|VOL_Q3",
]

FROZEN_DIRECTION_V88 = "BULLISH"

print("Frozen contexts:")
for x in FROZEN_CONTEXTS_V88:
    print("-", x)

print("Frozen direction:", FROZEN_DIRECTION_V88)
print("NO CONTEXT DEFINITIONS CHANGED")

preholdout_v88 = pd.concat(
    [
        train_context_v87,
        validation_context_v87,
    ]
).sort_values(
    "time_et"
).copy()

preholdout_days_v88 = sorted(
    preholdout_v88[
        "date_et"
    ].unique()
)

print(
    "Pre-holdout trading days:",
    len(preholdout_days_v88)
)

n_days_v88 = len(
    preholdout_days_v88
)

cut1_v88 = int(
    n_days_v88 * 0.25
)

cut2_v88 = int(
    n_days_v88 * 0.50
)

cut3_v88 = int(
    n_days_v88 * 0.75
)

ROBUST_PERIODS_V88 = [
    (
        "PERIOD_1",
        preholdout_days_v88[
            :cut1_v88
        ],
    ),
    (
        "PERIOD_2",
        preholdout_days_v88[
            cut1_v88:cut2_v88
        ],
    ),
    (
        "PERIOD_3",
        preholdout_days_v88[
            cut2_v88:cut3_v88
        ],
    ),
    (
        "PERIOD_4",
        preholdout_days_v88[
            cut3_v88:
        ],
    ),
]

print("Four chronological robustness periods frozen")

def frozen_context_stats_v88(
    frame,
    context
):

    sample = frame[
        frame["context_v87"]
        == context
    ].dropna(
        subset=[
            "future_return_60m"
        ]
    ).copy()

    if sample.empty:

        return {
            "observations": 0,
            "accuracy": 0.0,
            "avg_return": 0.0,
        }

    accuracy = (
        sample[
            "future_return_60m"
        ] > 0
    ).mean() * 100

    avg_return = (
        sample[
            "future_return_60m"
        ].mean() * 100
    )

    return {
        "observations": len(sample),
        "accuracy": accuracy,
        "avg_return": avg_return,
    }

print("Frozen-context evaluator ready")

robust_rows_v88 = []

for period_name, period_days in (
    ROBUST_PERIODS_V88
):

    period_frame = (
        preholdout_v88[
            preholdout_v88[
                "date_et"
            ].isin(period_days)
        ]
    )

    for context in (
        FROZEN_CONTEXTS_V88
    ):

        stats = (
            frozen_context_stats_v88(
                period_frame,
                context
            )
        )

        robust_rows_v88.append({
            "period": period_name,
            "context": context,
            **stats,
        })

robust_df_v88 = pd.DataFrame(
    robust_rows_v88
)

print("\nFROZEN CONTEXT ROBUSTNESS TABLE")

print(
    robust_df_v88.to_string(
        index=False
    )
)

context_robustness_v88 = (
    robust_df_v88
    .groupby("context")
    .agg(
        total_observations=(
            "observations",
            "sum"
        ),
        worst_accuracy=(
            "accuracy",
            "min"
        ),
        mean_accuracy=(
            "accuracy",
            "mean"
        ),
        worst_avg_return=(
            "avg_return",
            "min"
        ),
        mean_avg_return=(
            "avg_return",
            "mean"
        ),
    )
    .reset_index()
)

print("\nCONTEXT ROBUSTNESS SUMMARY")

print(
    context_robustness_v88
    .to_string(index=False)
)

context_robustness_v88[
    "robust_pass"
] = (
    (
        context_robustness_v88[
            "total_observations"
        ] >= 500
    )
    & (
        context_robustness_v88[
            "worst_accuracy"
        ] >= 50
    )
    & (
        context_robustness_v88[
            "mean_accuracy"
        ] >= 54
    )
    & (
        context_robustness_v88[
            "worst_avg_return"
        ] >= 0
    )
    & (
        context_robustness_v88[
            "mean_avg_return"
        ] > 0
    )
)

print("\nV8.8 ROBUSTNESS GATE")

print(
    context_robustness_v88[
        [
            "context",
            "total_observations",
            "worst_accuracy",
            "mean_accuracy",
            "worst_avg_return",
            "mean_avg_return",
            "robust_pass",
        ]
    ].to_string(index=False)
)

robust_survivors_v88 = (
    context_robustness_v88[
        context_robustness_v88[
            "robust_pass"
        ]
    ].copy()
)

print("\nV8.8 VERDICT")

if robust_survivors_v88.empty:

    verdict_v88 = (
        "NO FROZEN TIME-VOL CONTEXT "
        "SURVIVES ROBUSTNESS"
    )

else:

    verdict_v88 = (
        "FROZEN TIME-VOL CONTEXT "
        "SURVIVES ROBUSTNESS"
    )

    print(
        robust_survivors_v88
        .to_string(index=False)
    )

print("Verdict:", verdict_v88)
print("NO NEW CONTEXTS WERE SEARCHED")
print("NO PARAMETERS WERE RETUNED")
print("TRUE HOLDOUT REMAINS SEALED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

context_robustness_v88.to_csv(
    "spy_sentinel_time_vol_robustness_v88.csv",
    index=False
)

print("Robustness results saved")

print("\nV8.9 CORRECTED ONE-TIME TRUE HOLDOUT TEST")

FROZEN_HOLDOUT_CONTEXTS_V89 = [
    "MIDDAY|VOL_Q3",
    "AFTERNOON|VOL_Q3",
]

FROZEN_HOLDOUT_DIRECTION_V89 = "BULLISH"

print("FROZEN RULE — NO CHANGES ALLOWED")
print("Contexts:", FROZEN_HOLDOUT_CONTEXTS_V89)
print("Direction:", FROZEN_HOLDOUT_DIRECTION_V89)

holdout_context_v89 = holdout3_sealed.copy()

high_low_v89 = (
    holdout_context_v89["high"]
    - holdout_context_v89["low"]
)

high_close_v89 = (
    holdout_context_v89["high"]
    - holdout_context_v89["close"].shift(1)
).abs()

low_close_v89 = (
    holdout_context_v89["low"]
    - holdout_context_v89["close"].shift(1)
).abs()

holdout_context_v89["tr_v87"] = pd.concat(
    [
        high_low_v89,
        high_close_v89,
        low_close_v89,
    ],
    axis=1
).max(axis=1)

holdout_context_v89["atr14_v87"] = (
    holdout_context_v89["tr_v87"]
    .rolling(14)
    .mean()
    .shift(1)
)

holdout_context_v89["atr_pct_v87"] = (
    holdout_context_v89["atr14_v87"]
    / holdout_context_v89["close"]
)

print("Holdout ATR feature created using frozen formula")

holdout_context_v89 = label_context_v87(
    holdout_context_v89
)

print(
    "Holdout labeled using TRAIN-FROZEN "
    "volatility boundaries"
)

print(
    "Holdout trading days:",
    holdout_context_v89["date_et"].nunique()
)

holdout_candidate_v89 = (
    holdout_context_v89[
        holdout_context_v89[
            "context_v87"
        ].isin(
            FROZEN_HOLDOUT_CONTEXTS_V89
        )
    ]
    .dropna(
        subset=[
            "future_return_60m",
            "atr_pct_v87",
        ]
    )
    .copy()
)

print(
    "Frozen Holdout observations:",
    len(holdout_candidate_v89)
)

print("NO OTHER HOLDOUT CONTEXTS EVALUATED")

MIN_HOLDOUT_OBSERVATIONS_V89 = 500
MIN_HOLDOUT_ACCURACY_V89 = 54.0
MIN_HOLDOUT_CI_LOW_V89 = 50.0
MIN_HOLDOUT_AVG_RETURN_V89 = 0.0

print("\nPRE-REGISTERED HOLDOUT GATE")
print("Minimum observations: 500")
print("Minimum accuracy: 54.0%")
print("Minimum 95% CI lower bound: > 50.0%")
print("Average directional return must be > 0")

holdout_observations_v89 = len(
    holdout_candidate_v89
)

holdout_accuracy_v89 = (
    (
        holdout_candidate_v89[
            "future_return_60m"
        ] > 0
    ).mean() * 100
    if holdout_observations_v89
    else 0.0
)

holdout_avg_return_v89 = (
    holdout_candidate_v89[
        "future_return_60m"
    ].mean() * 100
    if holdout_observations_v89
    else 0.0
)

holdout_median_return_v89 = (
    holdout_candidate_v89[
        "future_return_60m"
    ].median() * 100
    if holdout_observations_v89
    else 0.0
)

holdout_ci_low_v89 = wilson_low_v72(
    holdout_accuracy_v89,
    holdout_observations_v89
)

print("\nTRUE HOLDOUT PERFORMANCE")
print(f"Observations: {holdout_observations_v89}")
print(f"Accuracy: {holdout_accuracy_v89:.2f}%")
print(f"Average return: {holdout_avg_return_v89:+.4f}%")
print(f"Median return: {holdout_median_return_v89:+.4f}%")
print(f"Holdout 95% CI low: {holdout_ci_low_v89:.2f}%")

holdout_pass_v89 = (
    holdout_observations_v89
    >= MIN_HOLDOUT_OBSERVATIONS_V89
    and holdout_accuracy_v89
    >= MIN_HOLDOUT_ACCURACY_V89
    and holdout_ci_low_v89
    > MIN_HOLDOUT_CI_LOW_V89
    and holdout_avg_return_v89
    > MIN_HOLDOUT_AVG_RETURN_V89
)

print("\nV8.9 TRUE HOLDOUT GATE")
print(
    "Frozen candidate passes:",
    holdout_pass_v89
)

print("\nV8.9 HOLDOUT VERDICT")

if holdout_pass_v89:
    holdout_verdict_v89 = (
        "TRUE HOLDOUT PASSES — "
        "PROCEED TO FINAL SAFETY/ECONOMIC GATE"
    )
else:
    holdout_verdict_v89 = (
        "TRUE HOLDOUT FAILS — "
        "REJECT FROZEN CANDIDATE"
    )

print("Verdict:", holdout_verdict_v89)
print("TRUE HOLDOUT HAS NOW BEEN CONSUMED")
print("DO NOT RETUNE THIS CANDIDATE TO HOLDOUT")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "contexts":
        "MIDDAY|VOL_Q3 + AFTERNOON|VOL_Q3",
    "direction":
        FROZEN_HOLDOUT_DIRECTION_V89,
    "observations":
        holdout_observations_v89,
    "accuracy":
        holdout_accuracy_v89,
    "ci_low":
        holdout_ci_low_v89,
    "avg_return":
        holdout_avg_return_v89,
    "median_return":
        holdout_median_return_v89,
    "passed":
        holdout_pass_v89,
    "verdict":
        holdout_verdict_v89,
}]).to_csv(
    "spy_sentinel_ONE_TIME_true_holdout_v89.csv",
    index=False
)

print("Permanent Holdout result saved")

print("\nV9.0 ROLLING WALK-FORWARD FRAMEWORK")

research_v90 = clean3.copy().sort_values(
    "time_et"
)

all_days_v90 = sorted(
    research_v90["date_et"].unique()
)

print(
    f"Historical research days: "
    f"{len(all_days_v90)}"
)

print(
    f"Historical end date: "
    f"{max(all_days_v90)}"
)

print("Post-Aug-14 data remains OUTSIDE this framework")

TRAIN_DAYS_V90 = 250
TEST_DAYS_V90 = 50
STEP_DAYS_V90 = 50

walk_windows_v90 = []

start_v90 = 0
window_number_v90 = 1

while (
    start_v90
    + TRAIN_DAYS_V90
    + TEST_DAYS_V90
    <= len(all_days_v90)
):

    train_days_window = all_days_v90[
        start_v90:
        start_v90 + TRAIN_DAYS_V90
    ]

    test_days_window = all_days_v90[
        start_v90 + TRAIN_DAYS_V90:
        start_v90 + TRAIN_DAYS_V90 + TEST_DAYS_V90
    ]

    walk_windows_v90.append({
        "window": window_number_v90,
        "train_days": train_days_window,
        "test_days": test_days_window,
    })

    start_v90 += STEP_DAYS_V90
    window_number_v90 += 1

print(
    f"Rolling windows created: "
    f"{len(walk_windows_v90)}"
)

print("\nROLLING WINDOW DATES")

for w in walk_windows_v90:

    print(
        f"Window {w['window']}: "
        f"TRAIN "
        f"{w['train_days'][0]} -> "
        f"{w['train_days'][-1]} | "
        f"TEST "
        f"{w['test_days'][0]} -> "
        f"{w['test_days'][-1]}"
    )

def build_context_features_v90(
    train_frame,
    test_frame
):

    train_frame = train_frame.copy()
    test_frame = test_frame.copy()

    for frame in [
        train_frame,
        test_frame,
    ]:

        high_low = (
            frame["high"] - frame["low"]
        )

        high_close = (
            frame["high"]
            - frame["close"].shift(1)
        ).abs()

        low_close = (
            frame["low"]
            - frame["close"].shift(1)
        ).abs()

        frame["tr_v90"] = pd.concat(
            [
                high_low,
                high_close,
                low_close,
            ],
            axis=1
        ).max(axis=1)

        frame["atr14_v90"] = (
            frame["tr_v90"]
            .rolling(14)
            .mean()
            .shift(1)
        )

        frame["atr_pct_v90"] = (
            frame["atr14_v90"]
            / frame["close"]
        )

    q1 = train_frame[
        "atr_pct_v90"
    ].quantile(0.25)

    q2 = train_frame[
        "atr_pct_v90"
    ].quantile(0.50)

    q3 = train_frame[
        "atr_pct_v90"
    ].quantile(0.75)

    return (
        train_frame,
        test_frame,
        (q1, q2, q3)
    )

print("Rolling feature builder ready")

def label_v90(
    frame,
    cuts
):

    q1, q2, q3 = cuts

    out = frame.copy()

    out["session_v90"] = np.select(
        [
            out["minutes_et"] < 660,
            out["minutes_et"] < 810,
        ],
        [
            "MORNING",
            "MIDDAY",
        ],
        default="AFTERNOON",
    )

    out["vol_v90"] = np.select(
        [
            out["atr_pct_v90"] < q1,
            out["atr_pct_v90"] < q2,
            out["atr_pct_v90"] < q3,
        ],
        [
            "VOL_Q1",
            "VOL_Q2",
            "VOL_Q3",
        ],
        default="VOL_Q4",
    )

    out["context_v90"] = (
        out["session_v90"]
        + "|"
        + out["vol_v90"]
    )

    return out

print("Rolling context labeler ready")

rolling_rows_v90 = []

for w in walk_windows_v90:

    train_frame = research_v90[
        research_v90[
            "date_et"
        ].isin(
            w["train_days"]
        )
    ].copy()

    test_frame = research_v90[
        research_v90[
            "date_et"
        ].isin(
            w["test_days"]
        )
    ].copy()

    train_frame, test_frame, cuts = (
        build_context_features_v90(
            train_frame,
            test_frame
        )
    )

    train_frame = label_v90(
        train_frame,
        cuts
    )

    test_frame = label_v90(
        test_frame,
        cuts
    )

    print(
        f"Prepared window "
        f"{w['window']}"
    )

print("\nV9.0 FRAMEWORK CHECK")

print(
    "Each test window occurs strictly "
    "after its training window"
)

print(
    "Volatility boundaries are derived "
    "from each training window only"
)

print(
    "No August 17-28 data has been loaded"
)

print(
    "No strategy performance evaluated yet"
)

print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([
    {
        "window": w["window"],
        "train_start": w["train_days"][0],
        "train_end": w["train_days"][-1],
        "test_start": w["test_days"][0],
        "test_end": w["test_days"][-1],
    }
    for w in walk_windows_v90
]).to_csv(
    "spy_sentinel_rolling_windows_v90.csv",
    index=False
)

print(
    "Rolling-window specification saved"
)

print("\nV9.1 ROLLING CONTEXT CANDIDATE TEST")

SESSIONS_V91 = [
    "MORNING",
    "MIDDAY",
    "AFTERNOON",
]

VOL_BUCKETS_V91 = [
    "VOL_Q1",
    "VOL_Q2",
    "VOL_Q3",
    "VOL_Q4",
]

DIRECTIONS_V91 = [
    "BULLISH",
    "BEARISH",
]

CANDIDATES_V91 = [
    (session, vol, direction)
    for session in SESSIONS_V91
    for vol in VOL_BUCKETS_V91
    for direction in DIRECTIONS_V91
]

print(
    "Predefined candidate count:",
    len(CANDIDATES_V91)
)

print("AUGUST 17-28 FRESH DATA REMAINS UNTOUCHED")

def add_context_v91(
    frame,
    q1,
    q2,
    q3,
):

    out = frame.copy()

    high_low = (
        out["high"] - out["low"]
    )

    high_close = (
        out["high"]
        - out["close"].shift(1)
    ).abs()

    low_close = (
        out["low"]
        - out["close"].shift(1)
    ).abs()

    out["tr_v91"] = pd.concat(
        [
            high_low,
            high_close,
            low_close,
        ],
        axis=1
    ).max(axis=1)

    out["atr_v91"] = (
        out["tr_v91"]
        .rolling(14)
        .mean()
        .shift(1)
    )

    out["atr_pct_v91"] = (
        out["atr_v91"]
        / out["close"]
    )

    out["session_v91"] = np.select(
        [
            out["minutes_et"] < 660,
            out["minutes_et"] < 810,
        ],
        [
            "MORNING",
            "MIDDAY",
        ],
        default="AFTERNOON",
    )

    out["vol_v91"] = np.select(
        [
            out["atr_pct_v91"] < q1,
            out["atr_pct_v91"] < q2,
            out["atr_pct_v91"] < q3,
        ],
        [
            "VOL_Q1",
            "VOL_Q2",
            "VOL_Q3",
        ],
        default="VOL_Q4",
    )

    return out

print("Rolling context builder ready")

rolling_rows_v91 = []

for window_number, w in enumerate(
    walk_windows_v90,
    start=1
):

    train_frame = clean3[
        clean3["date_et"].isin(
            w["train_days"]
        )
    ].copy()

    test_frame = clean3[
        clean3["date_et"].isin(
            w["test_days"]
        )
    ].copy()

    train_temp = add_context_v91(
        train_frame,
        0,
        0,
        0,
    )

    q1 = train_temp[
        "atr_pct_v91"
    ].quantile(0.25)

    q2 = train_temp[
        "atr_pct_v91"
    ].quantile(0.50)

    q3 = train_temp[
        "atr_pct_v91"
    ].quantile(0.75)

    test_context = add_context_v91(
        test_frame,
        q1,
        q2,
        q3,
    )

    print(
        f"Prepared evaluation window "
        f"{window_number}"
    )

    for session, vol, direction in (
        CANDIDATES_V91
    ):

        sample = test_context[
            (
                test_context[
                    "session_v91"
                ] == session
            )
            & (
                test_context[
                    "vol_v91"
                ] == vol
            )
        ].dropna(
            subset=[
                "future_return_60m"
            ]
        ).copy()

        sample = (
            sample
            .sort_values("time_et")
            .groupby(
                "date_et",
                as_index=False
            )
            .first()
        )

        if direction == "BULLISH":

            wins = (
                sample[
                    "future_return_60m"
                ] > 0
            )

            signed = (
                sample[
                    "future_return_60m"
                ]
            )

        else:

            wins = (
                sample[
                    "future_return_60m"
                ] < 0
            )

            signed = (
                -sample[
                    "future_return_60m"
                ]
            )

        rolling_rows_v91.append({
            "window": window_number,
            "session": session,
            "vol": vol,
            "direction": direction,
            "observations": len(sample),
            "accuracy": (
                wins.mean() * 100
                if len(sample)
                else 0.0
            ),
            "avg_return": (
                signed.mean() * 100
                if len(sample)
                else 0.0
            ),
        })

rolling_df_v91 = pd.DataFrame(
    rolling_rows_v91
)

print("All rolling candidate tests complete")

summary_rows_v91 = []

for (
    session,
    vol,
    direction
) in CANDIDATES_V91:

    x = rolling_df_v91[
        (
            rolling_df_v91[
                "session"
            ] == session
        )
        & (
            rolling_df_v91[
                "vol"
            ] == vol
        )
        & (
            rolling_df_v91[
                "direction"
            ] == direction
        )
    ].copy()

    valid = x[
        x["observations"] > 0
    ].copy()

    total_obs = int(
        valid["observations"].sum()
    )

    weighted_wins = (
        (
            valid["accuracy"] / 100
        )
        * valid["observations"]
    ).sum()

    weighted_accuracy = (
        weighted_wins
        / total_obs
        * 100
        if total_obs
        else 0.0
    )

    weighted_return = (
        (
            valid["avg_return"]
            * valid["observations"]
        ).sum()
        / total_obs
        if total_obs
        else 0.0
    )

    summary_rows_v91.append({
        "candidate":
            f"{session}|{vol}|{direction}",
        "windows": len(valid),
        "total_observations": total_obs,
        "weighted_accuracy":
            weighted_accuracy,
        "avg_directional_return":
            weighted_return,
        "positive_return_windows":
            int(
                (
                    valid["avg_return"] > 0
                ).sum()
            ),
        "worst_window_accuracy":
            (
                valid["accuracy"].min()
                if len(valid)
                else 0.0
            ),
    })

summary_v91 = pd.DataFrame(
    summary_rows_v91
)

print("\nROLLING CANDIDATE SUMMARY")

print(
    summary_v91
    .sort_values(
        "weighted_accuracy",
        ascending=False
    )
    .to_string(index=False)
)

def wilson_v91(
    accuracy_pct,
    n,
    z=1.96,
):

    if n <= 0:
        return 0.0

    p = accuracy_pct / 100

    denominator = (
        1 + z**2 / n
    )

    center = (
        p + z**2 / (2 * n)
    ) / denominator

    margin = (
        z * np.sqrt(
            p * (1 - p) / n
            + z**2 / (4 * n**2)
        )
        / denominator
    )

    return (
        center - margin
    ) * 100

summary_v91["ci_low"] = (
    summary_v91.apply(
        lambda r: wilson_v91(
            r["weighted_accuracy"],
            int(
                r["total_observations"]
            ),
        ),
        axis=1,
    )
)

print("Rolling confidence bounds calculated")

print("\nPRE-REGISTERED V9.1 GATE")

print("Required windows: >= 8 of 10")
print("Required observations: >= 100")
print("Weighted accuracy: >= 54%")
print("95% CI lower bound: > 50%")
print("Positive-return windows: >= 7")
print("Worst window accuracy: >= 45%")
print("Average directional return: > 0")

summary_v91["rolling_pass"] = (
    (summary_v91["windows"] >= 8)
    & (
        summary_v91[
            "total_observations"
        ] >= 100
    )
    & (
        summary_v91[
            "weighted_accuracy"
        ] >= 54
    )
    & (
        summary_v91[
            "ci_low"
        ] > 50
    )
    & (
        summary_v91[
            "positive_return_windows"
        ] >= 7
    )
    & (
        summary_v91[
            "worst_window_accuracy"
        ] >= 45
    )
    & (
        summary_v91[
            "avg_directional_return"
        ] > 0
    )
)

print("\nV9.1 ROLLING GATE")

print(
    summary_v91[
        [
            "candidate",
            "total_observations",
            "weighted_accuracy",
            "ci_low",
            "positive_return_windows",
            "worst_window_accuracy",
            "avg_directional_return",
            "rolling_pass",
        ]
    ]
    .sort_values(
        "weighted_accuracy",
        ascending=False
    )
    .to_string(index=False)
)

survivors_v91 = summary_v91[
    summary_v91[
        "rolling_pass"
    ]
].copy()

print("\nV9.1 CANDIDATE VERDICT")

if survivors_v91.empty:

    frozen_candidate_v91 = "NONE"

    verdict_v91 = (
        "NO ROLLING CANDIDATE SURVIVES"
    )

else:

    winner_v91 = (
        survivors_v91
        .sort_values(
            [
                "ci_low",
                "weighted_accuracy",
                "total_observations",
            ],
            ascending=False,
        )
        .iloc[0]
    )

    frozen_candidate_v91 = (
        winner_v91["candidate"]
    )

    verdict_v91 = (
        "FREEZE CANDIDATE FOR "
        "FRESH SHADOW-FORWARD TEST"
    )

    print(
        "Frozen candidate:",
        frozen_candidate_v91
    )

print("Verdict:", verdict_v91)
print("AUGUST 17-28 DATA REMAINS UNTOUCHED")
print("NO FRESH-DATA PERFORMANCE INSPECTED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

rolling_df_v91.to_csv(
    "spy_sentinel_rolling_windows_v91.csv",
    index=False,
)

summary_v91.to_csv(
    "spy_sentinel_rolling_summary_v91.csv",
    index=False,
)

print("Rolling candidate research saved")

print("\nV9.2 NESTED ROLLING SELECTION TEST")

print("RULE:")
print("1. Rank candidates using TRAIN portion only")
print("2. Freeze one candidate per rolling window")
print("3. Evaluate only that candidate on next TEST window")
print("4. Fresh August 17-28 data remains untouched")

def evaluate_context_candidate_v92(
    frame,
    session,
    vol,
    direction,
):

    sample = frame[
        (frame["session_v91"] == session)
        & (frame["vol_v91"] == vol)
    ].dropna(
        subset=["future_return_60m"]
    ).copy()

    sample = (
        sample
        .sort_values("time_et")
        .groupby(
            "date_et",
            as_index=False
        )
        .first()
    )

    if direction == "BULLISH":
        wins = sample["future_return_60m"] > 0
        signed = sample["future_return_60m"]
    else:
        wins = sample["future_return_60m"] < 0
        signed = -sample["future_return_60m"]

    n = len(sample)

    accuracy = (
        wins.mean() * 100
        if n
        else 0.0
    )

    avg_return = (
        signed.mean() * 100
        if n
        else 0.0
    )

    ci_low = wilson_v91(
        accuracy,
        n,
    )

    return {
        "observations": n,
        "accuracy": accuracy,
        "avg_return": avg_return,
        "ci_low": ci_low,
    }

print("Nested candidate evaluator ready")

nested_rows_v92 = []

for window_number, w in enumerate(
    walk_windows_v90,
    start=1
):

    train_frame = clean3[
        clean3["date_et"].isin(
            w["train_days"]
        )
    ].copy()

    test_frame = clean3[
        clean3["date_et"].isin(
            w["test_days"]
        )
    ].copy()

    temp_train = add_context_v91(
        train_frame,
        0,
        0,
        0,
    )

    q1 = temp_train["atr_pct_v91"].quantile(0.25)
    q2 = temp_train["atr_pct_v91"].quantile(0.50)
    q3 = temp_train["atr_pct_v91"].quantile(0.75)

    train_context = add_context_v91(
        train_frame,
        q1,
        q2,
        q3,
    )

    test_context = add_context_v91(
        test_frame,
        q1,
        q2,
        q3,
    )

    print(
        f"Nested window {window_number} prepared"
    )

    training_candidates = []

    for session, vol, direction in CANDIDATES_V91:

        stats = evaluate_context_candidate_v92(
            train_context,
            session,
            vol,
            direction,
        )

        if (
            stats["observations"] >= 100
            and stats["accuracy"] >= 52
            and stats["avg_return"] > 0
        ):

            training_candidates.append({
                "session": session,
                "vol": vol,
                "direction": direction,
                **stats,
            })

    if not training_candidates:

        nested_rows_v92.append({
            "window": window_number,
            "candidate": "ABSTAIN",
            "test_observations": 0,
            "test_accuracy": 0.0,
            "test_avg_return": 0.0,
        })

        print(
            f"Window {window_number}: ABSTAIN"
        )

        continue

    training_rank = pd.DataFrame(
        training_candidates
    ).sort_values(
        [
            "ci_low",
            "accuracy",
            "observations",
        ],
        ascending=False,
    )

    chosen = training_rank.iloc[0]

    frozen_session = chosen["session"]
    frozen_vol = chosen["vol"]
    frozen_direction = chosen["direction"]

    frozen_name = (
        f"{frozen_session}|"
        f"{frozen_vol}|"
        f"{frozen_direction}"
    )

    test_stats = evaluate_context_candidate_v92(
        test_context,
        frozen_session,
        frozen_vol,
        frozen_direction,
    )

    nested_rows_v92.append({
        "window": window_number,
        "candidate": frozen_name,
        "train_observations":
            chosen["observations"],
        "train_accuracy":
            chosen["accuracy"],
        "train_ci_low":
            chosen["ci_low"],
        "test_observations":
            test_stats["observations"],
        "test_accuracy":
            test_stats["accuracy"],
        "test_avg_return":
            test_stats["avg_return"],
    })

    print(
        f"Window {window_number}: "
        f"{frozen_name}"
    )

nested_df_v92 = pd.DataFrame(
    nested_rows_v92
)

print("\nNESTED ROLLING RESULTS")

print(
    nested_df_v92.to_string(
        index=False
    )
)

active_v92 = nested_df_v92[
    nested_df_v92["candidate"]
    != "ABSTAIN"
].copy()

active_windows_v92 = len(active_v92)

total_test_obs_v92 = int(
    active_v92[
        "test_observations"
    ].sum()
)

weighted_wins_v92 = (
    (
        active_v92[
            "test_accuracy"
        ] / 100
    )
    * active_v92[
        "test_observations"
    ]
).sum()

weighted_accuracy_v92 = (
    weighted_wins_v92
    / total_test_obs_v92
    * 100
    if total_test_obs_v92
    else 0.0
)

weighted_return_v92 = (
    (
        active_v92[
            "test_avg_return"
        ]
        * active_v92[
            "test_observations"
        ]
    ).sum()
    / total_test_obs_v92
    if total_test_obs_v92
    else 0.0
)

positive_windows_v92 = int(
    (
        active_v92[
            "test_avg_return"
        ] > 0
    ).sum()
)

nested_ci_low_v92 = wilson_v91(
    weighted_accuracy_v92,
    total_test_obs_v92,
)

print("\nV9.2 AGGREGATE OUT-OF-SAMPLE")

print(
    f"Active windows: "
    f"{active_windows_v92}"
)

print(
    f"Total test observations: "
    f"{total_test_obs_v92}"
)

print(
    f"Weighted accuracy: "
    f"{weighted_accuracy_v92:.2f}%"
)

print(
    f"95% CI low: "
    f"{nested_ci_low_v92:.2f}%"
)

print(
    f"Average directional return: "
    f"{weighted_return_v92:+.4f}%"
)

print(
    f"Positive-return windows: "
    f"{positive_windows_v92}"
)

nested_pass_v92 = (
    active_windows_v92 >= 8
    and total_test_obs_v92 >= 100
    and weighted_accuracy_v92 >= 54
    and nested_ci_low_v92 > 50
    and weighted_return_v92 > 0
    and positive_windows_v92 >= 7
)

print("\nV9.2 NESTED SELECTION GATE")

if nested_pass_v92:

    verdict_v92 = (
        "FREEZE ADAPTIVE SELECTION PROCESS "
        "FOR FRESH SHADOW-FORWARD TEST"
    )

else:

    verdict_v92 = (
        "ADAPTIVE SELECTION PROCESS "
        "DOES NOT GENERALIZE"
    )

print("Pass:", nested_pass_v92)
print("Verdict:", verdict_v92)
print("AUGUST 17-28 DATA REMAINS UNTOUCHED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

nested_df_v92.to_csv(
    "spy_sentinel_nested_rolling_v92.csv",
    index=False,
)

print("Nested rolling research saved")

print("\nV9.3 FULL-HISTORY MULTI-MARKET FEATURE REBUILD")

print("SOURCE DATA:")
print("- SPY verified 3-year 5-minute data")
print("- QQQ verified 3-year 5-minute data")
print("- XLK verified 3-year 5-minute data")
print("- XLF verified 3-year 5-minute data")

print("GOAL:")
print("Rebuild clean lagged cross-market features through Aug 14, 2026")
print("Then evaluate only through rolling historical windows")

print("AUGUST 17-28 REMAINS UNTOUCHED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

print("\nV9.3 LOAD VERIFIED MULTI-MARKET DATA")

from pathlib import Path

DATA_DIR_V93 = (
    Path.home()
    / "Documents"
    / "ai trading bot"
)

SYMBOLS_V93 = [
    "SPY",
    "QQQ",
    "XLK",
    "XLF",
]

def load_verified_v93(symbol):

    f = (
        DATA_DIR_V93
        / f"{symbol}_5min_3years_clean.csv"
    )

    df = pd.read_csv(f)

    time_col = next(
        c for c in df.columns
        if "time" in c.lower()
        or "date" in c.lower()
    )

    df["timestamp_utc"] = pd.to_datetime(
        df[time_col],
        utc=True
    )

    df = df.sort_values(
        "timestamp_utc"
    ).copy()

    df["time_et_v93"] = (
        df["timestamp_utc"]
        .dt.tz_convert(
            "America/New_York"
        )
    )

    df["date_et_v93"] = (
        df["time_et_v93"].dt.date
    )

    return df

market_v93 = {}

for symbol in SYMBOLS_V93:

    market_v93[symbol] = (
        load_verified_v93(symbol)
    )

    print(
        symbol,
        "rows:",
        len(market_v93[symbol])
    )

print("\nBUILD LAGGED RETURNS")

for symbol in SYMBOLS_V93:

    df = market_v93[symbol]

    for bars, label in [
        (1, "5"),
        (3, "15"),
        (6, "30"),
        (12, "60"),
    ]:

        df[
            f"{symbol.lower()}_ret{label}_lag"
        ] = (
            df.groupby(
                "date_et_v93"
            )["close"]
            .pct_change(bars)
            .shift(1)
        )

    market_v93[symbol] = df

print("Lagged 5/15/30/60-minute returns created")

print("\nMERGE MARKETS")

spy_v93 = market_v93["SPY"].copy()

multi_v93 = spy_v93[
    [
        "timestamp_utc",
        "time_et_v93",
        "date_et_v93",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "spy_ret5_lag",
        "spy_ret15_lag",
        "spy_ret30_lag",
        "spy_ret60_lag",
    ]
].copy()

for symbol in [
    "QQQ",
    "XLK",
    "XLF",
]:

    s = symbol.lower()

    keep = [
        "timestamp_utc",
        f"{s}_ret5_lag",
        f"{s}_ret15_lag",
        f"{s}_ret30_lag",
        f"{s}_ret60_lag",
    ]

    multi_v93 = multi_v93.merge(
        market_v93[symbol][keep],
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )

print(
    "Aligned rows:",
    len(multi_v93)
)

print("\nBUILD RELATIVE-STRENGTH FEATURES")

for symbol in [
    "QQQ",
    "XLK",
    "XLF",
]:

    s = symbol.lower()

    for label in [
        "5",
        "15",
        "30",
        "60",
    ]:

        multi_v93[
            f"{s}_relative{label}"
        ] = (
            multi_v93[
                f"{s}_ret{label}_lag"
            ]
            - multi_v93[
                f"spy_ret{label}_lag"
            ]
        )

print("Relative-strength features created")

print("\nBUILD CROSS-MARKET BREADTH FEATURES")

for label in [
    "5",
    "15",
    "30",
    "60",
]:

    cols = [
        f"qqq_ret{label}_lag",
        f"xlk_ret{label}_lag",
        f"xlf_ret{label}_lag",
    ]

    multi_v93[
        f"breadth_positive_{label}"
    ] = (
        multi_v93[cols] > 0
    ).sum(axis=1)

    multi_v93[
        f"breadth_mean_{label}"
    ] = (
        multi_v93[cols].mean(axis=1)
    )

    multi_v93[
        f"breadth_dispersion_{label}"
    ] = (
        multi_v93[cols].std(
            axis=1
        )
    )

print(
    "Breadth count, mean, and dispersion features created"
)

print("\nBUILD SPY TARGET SAFELY")

future_close_v93 = (
    multi_v93["close"].shift(-12)
)

future_date_v93 = (
    multi_v93[
        "date_et_v93"
    ].shift(-12)
)

multi_v93[
    "future_return_60m"
] = np.where(
    multi_v93["date_et_v93"]
    == future_date_v93,
    future_close_v93
    / multi_v93["close"]
    - 1,
    np.nan
)

print(
    "Same-day 60-minute target created"
)

print("\nFRESH-DATA BOUNDARY CHECK")

max_history_date_v93 = (
    pd.to_datetime(
        multi_v93["date_et_v93"]
    ).max()
)

print(
    "Latest row in rebuilt dataset:",
    max_history_date_v93.date()
)

fresh_safe_v93 = (
    max_history_date_v93
    <= pd.Timestamp(
        "2026-08-14"
    )
)

print(
    "Stops on/before Aug 14:",
    fresh_safe_v93
)

if not fresh_safe_v93:
    raise RuntimeError(
        "STOP: fresh Aug 17-28 data was loaded"
    )

FEATURES_V93 = [
    c for c in multi_v93.columns
    if (
        "_lag" in c
        or "_relative" in c
        or c.startswith(
            "breadth_"
        )
    )
]

print("\nV9.3 FEATURE AUDIT")
print(
    "Feature count:",
    len(FEATURES_V93)
)

for c in FEATURES_V93:
    print("-", c)

print(
    "Duplicate timestamps:",
    multi_v93[
        "timestamp_utc"
    ].duplicated().sum()
)

print(
    "Missing target rows:",
    multi_v93[
        "future_return_60m"
    ].isna().sum()
)

multi_v93.to_csv(
    "spy_sentinel_full_history_multimarket_v93.csv",
    index=False,
)

print("\nV9.3 REBUILD COMPLETE")
print(
    "Rows:",
    len(multi_v93)
)
print(
    "Predictive features:",
    len(FEATURES_V93)
)
print(
    "NO STRATEGY OR MODEL TESTED"
)
print(
    "AUGUST 17-28 REMAINS UNTOUCHED"
)
print(
    "PAPER TRADING: LOCKED"
)
print(
    "LIVE TRADING: LOCKED"
)
print(
    "Full-history multi-market feature table saved"
)

print("\nV9.4 FULL-HISTORY MULTI-MARKET ROLLING MODEL")

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    roc_auc_score,
)

model_data_v94 = multi_v93.replace(
    [np.inf, -np.inf],
    np.nan
).dropna(
    subset=FEATURES_V93
    + ["future_return_60m"]
).copy()

model_data_v94["target_v94"] = (
    model_data_v94[
        "future_return_60m"
    ] > 0
).astype(int)

print("Usable model rows:", len(model_data_v94))
print("Features:", len(FEATURES_V93))
print("Fresh Aug 17-28 still untouched")

def make_model_v94():

    return HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=15,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=42,
    )

print("Fixed model specification registered")

rolling_model_rows_v94 = []

for window_number, w in enumerate(
    walk_windows_v90,
    start=1
):

    train_v94 = model_data_v94[
        model_data_v94[
            "date_et_v93"
        ].isin(
            w["train_days"]
        )
    ].copy()

    test_v94 = model_data_v94[
        model_data_v94[
            "date_et_v93"
        ].isin(
            w["test_days"]
        )
    ].copy()

    model_v94 = make_model_v94()

    model_v94.fit(
        train_v94[FEATURES_V93],
        train_v94["target_v94"],
    )

    prob_v94 = model_v94.predict_proba(
        test_v94[FEATURES_V93]
    )[:, 1]

    pred_v94 = (
        prob_v94 >= 0.50
    ).astype(int)

    bal_v94 = (
        balanced_accuracy_score(
            test_v94["target_v94"],
            pred_v94,
        ) * 100
    )

    auc_v94 = (
        roc_auc_score(
            test_v94["target_v94"],
            prob_v94,
        ) * 100
    )

    confident_v94 = (
        (prob_v94 >= 0.55)
        | (prob_v94 <= 0.45)
    )

    conf_prob_v94 = (
        prob_v94[
            confident_v94
        ]
    )

    actual_v94 = (
        test_v94[
            "target_v94"
        ].to_numpy()[
            confident_v94
        ]
    )

    returns_v94 = (
        test_v94[
            "future_return_60m"
        ].to_numpy()[
            confident_v94
        ]
    )

    if len(conf_prob_v94):

        conf_pred_v94 = (
            conf_prob_v94 >= 0.50
        ).astype(int)

        conf_accuracy_v94 = (
            conf_pred_v94
            == actual_v94
        ).mean() * 100

        signed_returns_v94 = np.where(
            conf_pred_v94 == 1,
            returns_v94,
            -returns_v94,
        )

        conf_avg_return_v94 = (
            signed_returns_v94.mean()
            * 100
        )

    else:

        conf_accuracy_v94 = 0.0
        conf_avg_return_v94 = 0.0

    rolling_model_rows_v94.append({
        "window": window_number,
        "train_rows": len(train_v94),
        "test_rows": len(test_v94),
        "balanced_accuracy": bal_v94,
        "auc": auc_v94,
        "confident_signals":
            len(conf_prob_v94),
        "confident_accuracy":
            conf_accuracy_v94,
        "confident_avg_return":
            conf_avg_return_v94,
    })

    print(
        f"Window {window_number}: "
        f"bal {bal_v94:.2f}% | "
        f"AUC {auc_v94:.2f}% | "
        f"conf {len(conf_prob_v94)} | "
        f"acc {conf_accuracy_v94:.2f}%"
    )

rolling_model_df_v94 = pd.DataFrame(
    rolling_model_rows_v94
)

print("\nV9.4 ROLLING MODEL RESULTS")

print(
    rolling_model_df_v94.to_string(
        index=False
    )
)

total_conf_v94 = int(
    rolling_model_df_v94[
        "confident_signals"
    ].sum()
)

weighted_correct_v94 = (
    (
        rolling_model_df_v94[
            "confident_accuracy"
        ] / 100
    )
    * rolling_model_df_v94[
        "confident_signals"
    ]
).sum()

weighted_conf_accuracy_v94 = (
    weighted_correct_v94
    / total_conf_v94
    * 100
    if total_conf_v94
    else 0.0
)

weighted_conf_return_v94 = (
    (
        rolling_model_df_v94[
            "confident_avg_return"
        ]
        * rolling_model_df_v94[
            "confident_signals"
        ]
    ).sum()
    / total_conf_v94
    if total_conf_v94
    else 0.0
)

positive_windows_v94 = int(
    (
        rolling_model_df_v94[
            "confident_avg_return"
        ] > 0
    ).sum()
)

print("\nV9.4 AGGREGATE OUT-OF-SAMPLE")
print("Confident signals:", total_conf_v94)
print(
    f"Weighted confident accuracy: "
    f"{weighted_conf_accuracy_v94:.2f}%"
)
print(
    f"Weighted directional return: "
    f"{weighted_conf_return_v94:+.4f}%"
)
print(
    "Positive-return windows:",
    positive_windows_v94,
)

ci_low_v94 = wilson_v91(
    weighted_conf_accuracy_v94,
    total_conf_v94,
)

print(
    f"95% CI lower bound: "
    f"{ci_low_v94:.2f}%"
)

mean_bal_v94 = (
    rolling_model_df_v94[
        "balanced_accuracy"
    ].mean()
)

mean_auc_v94 = (
    rolling_model_df_v94[
        "auc"
    ].mean()
)

worst_bal_v94 = (
    rolling_model_df_v94[
        "balanced_accuracy"
    ].min()
)

print(
    f"Mean balanced accuracy: "
    f"{mean_bal_v94:.2f}%"
)

print(
    f"Worst balanced accuracy: "
    f"{worst_bal_v94:.2f}%"
)

print(
    f"Mean AUC: "
    f"{mean_auc_v94:.2f}%"
)

rolling_model_pass_v94 = (
    total_conf_v94 >= 150
    and weighted_conf_accuracy_v94 >= 54
    and ci_low_v94 > 50
    and weighted_conf_return_v94 > 0
    and positive_windows_v94 >= 7
    and mean_bal_v94 >= 52
    and mean_auc_v94 >= 52
    and worst_bal_v94 >= 47
)

print("\nV9.4 ROLLING MODEL GATE")

if rolling_model_pass_v94:

    verdict_v94 = (
        "FREEZE MULTI-MARKET MODEL FOR "
        "FRESH AUGUST SHADOW TEST"
    )

else:

    verdict_v94 = (
        "MULTI-MARKET MODEL "
        "DOES NOT GENERALIZE"
    )

print("Pass:", rolling_model_pass_v94)
print("Verdict:", verdict_v94)
print("AUGUST 17-28 REMAINS UNTOUCHED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

rolling_model_df_v94.to_csv(
    "spy_sentinel_multimarket_rolling_v94.csv",
    index=False,
)

print("Rolling multi-market research saved")

print("\nV10.0 KOTEGAWA EXTREME-DISLOCATION ENGINE")

dislocation_v100 = clean3.copy()

dislocation_v100["ret5_v100"] = (
    dislocation_v100["close"]
    .pct_change()
)

dislocation_v100["ret30_v100"] = (
    dislocation_v100["close"]
    .pct_change(6)
    .shift(1)
)

dislocation_v100["ret60_v100"] = (
    dislocation_v100["close"]
    .pct_change(12)
    .shift(1)
)

print("Lagged return features created")

dislocation_v100["vol60_v100"] = (
    dislocation_v100["ret5_v100"]
    .rolling(12)
    .std()
    .shift(1)
)

dislocation_v100["vol20day_v100"] = (
    dislocation_v100["ret5_v100"]
    .rolling(20 * 78)
    .std()
    .shift(1)
)

print("Short and long volatility features created")

dislocation_v100["ema20_v100"] = (
    dislocation_v100["close"]
    .ewm(
        span=20,
        adjust=False
    )
    .mean()
)

dislocation_v100["ema50_v100"] = (
    dislocation_v100["close"]
    .ewm(
        span=50,
        adjust=False
    )
    .mean()
)

dislocation_v100["stretch20_v100"] = (
    (
        dislocation_v100["close"]
        - dislocation_v100["ema20_v100"]
    )
    / dislocation_v100["close"]
)

dislocation_v100["stretch50_v100"] = (
    (
        dislocation_v100["close"]
        - dislocation_v100["ema50_v100"]
    )
    / dislocation_v100["close"]
)

print("EMA dislocation features created")

dislocation_v100["dislocation30_v100"] = (
    dislocation_v100["ret30_v100"]
    / (
        dislocation_v100["vol60_v100"]
        * np.sqrt(6)
    )
)

dislocation_v100["dislocation60_v100"] = (
    dislocation_v100["ret60_v100"]
    / (
        dislocation_v100["vol60_v100"]
        * np.sqrt(12)
    )
)

dislocation_v100 = dislocation_v100.replace(
    [np.inf, -np.inf],
    np.nan
)

print("Volatility-adjusted dislocation scores created")

DISLOCATION_LEVELS_V100 = [
    1.5,
    2.0,
    2.5,
]

print("\nPREDEFINED DISLOCATION LEVELS")

for level in DISLOCATION_LEVELS_V100:
    print(
        f"- {level:.1f} standard-volatility units"
    )

print("NO THRESHOLD HAS BEEN SELECTED USING HOLDOUT")

def build_dislocation_signal_v100(
    frame,
    level,
):

    sample = frame.copy()

    sample["dislocation_signal_v100"] = (
        "NO TRADE"
    )

    oversold = (
        sample["dislocation60_v100"]
        <= -level
    )

    overbought = (
        sample["dislocation60_v100"]
        >= level
    )

    sample.loc[
        oversold,
        "dislocation_signal_v100"
    ] = "BULLISH"

    sample.loc[
        overbought,
        "dislocation_signal_v100"
    ] = "BEARISH"

    return sample

print("Extreme-dislocation signal builder ready")

rolling_dislocation_rows_v100 = []

for window_number, w in enumerate(
    walk_windows_v90,
    start=1
):

    test_frame = dislocation_v100[
        dislocation_v100[
            "date_et"
        ].isin(
            w["test_days"]
        )
    ].copy()

    for level in DISLOCATION_LEVELS_V100:

        test_signal = (
            build_dislocation_signal_v100(
                test_frame,
                level,
            )
        )

        signals = test_signal[
            test_signal[
                "dislocation_signal_v100"
            ].isin(
                ["BULLISH", "BEARISH"]
            )
        ].dropna(
            subset=[
                "future_return_60m"
            ]
        ).copy()

        signals = (
            signals
            .sort_values("time_et")
            .groupby(
                "date_et",
                as_index=False
            )
            .first()
        )

        if len(signals):

            wins = (
                (
                    (
                        signals[
                            "dislocation_signal_v100"
                        ] == "BULLISH"
                    )
                    & (
                        signals[
                            "future_return_60m"
                        ] > 0
                    )
                )
                |
                (
                    (
                        signals[
                            "dislocation_signal_v100"
                        ] == "BEARISH"
                    )
                    & (
                        signals[
                            "future_return_60m"
                        ] < 0
                    )
                )
            )

            signed = np.where(
                signals[
                    "dislocation_signal_v100"
                ] == "BULLISH",
                signals[
                    "future_return_60m"
                ],
                -signals[
                    "future_return_60m"
                ],
            )

            accuracy = (
                wins.mean() * 100
            )

            avg_return = (
                signed.mean() * 100
            )

        else:

            accuracy = 0.0
            avg_return = 0.0

        rolling_dislocation_rows_v100.append({
            "window": window_number,
            "level": level,
            "signals": len(signals),
            "accuracy": accuracy,
            "avg_return": avg_return,
        })

print("Rolling dislocation tests completed")

dislocation_results_v100 = pd.DataFrame(
    rolling_dislocation_rows_v100
)

summary_rows_v100 = []

for level in DISLOCATION_LEVELS_V100:

    x = dislocation_results_v100[
        dislocation_results_v100[
            "level"
        ] == level
    ].copy()

    total_signals = int(
        x["signals"].sum()
    )

    weighted_accuracy = (
        (
            (
                x["accuracy"] / 100
            )
            * x["signals"]
        ).sum()
        / total_signals
        * 100
        if total_signals
        else 0.0
    )

    weighted_return = (
        (
            x["avg_return"]
            * x["signals"]
        ).sum()
        / total_signals
        if total_signals
        else 0.0
    )

    positive_windows = int(
        (
            x["avg_return"] > 0
        ).sum()
    )

    ci_low = wilson_v91(
        weighted_accuracy,
        total_signals,
    )

    summary_rows_v100.append({
        "level": level,
        "signals": total_signals,
        "accuracy": weighted_accuracy,
        "ci_low": ci_low,
        "avg_return": weighted_return,
        "positive_windows": positive_windows,
    })

summary_dislocation_v100 = pd.DataFrame(
    summary_rows_v100
)

print("\nV10.0 DISLOCATION SUMMARY")

print(
    summary_dislocation_v100
    .to_string(index=False)
)

summary_dislocation_v100[
    "rolling_pass"
] = (
    (
        summary_dislocation_v100[
            "signals"
        ] >= 100
    )
    & (
        summary_dislocation_v100[
            "accuracy"
        ] >= 54
    )
    & (
        summary_dislocation_v100[
            "ci_low"
        ] > 50
    )
    & (
        summary_dislocation_v100[
            "avg_return"
        ] > 0
    )
    & (
        summary_dislocation_v100[
            "positive_windows"
        ] >= 7
    )
)

print("\nV10.0 KOTEGAWA-STYLE GATE")

print(
    summary_dislocation_v100[
        [
            "level",
            "signals",
            "accuracy",
            "ci_low",
            "avg_return",
            "positive_windows",
            "rolling_pass",
        ]
    ].to_string(index=False)
)

survivors_v100 = (
    summary_dislocation_v100[
        summary_dislocation_v100[
            "rolling_pass"
        ]
    ]
)

if survivors_v100.empty:

    verdict_v100 = (
        "EXTREME-DISLOCATION FAMILY "
        "DOES NOT GENERALIZE"
    )

else:

    verdict_v100 = (
        "FREEZE EXTREME-DISLOCATION "
        "CANDIDATE FOR FRESH SHADOW TEST"
    )

print("\nVerdict:", verdict_v100)
print("AUGUST 17-28 REMAINS UNTOUCHED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

dislocation_results_v100.to_csv(
    "spy_sentinel_dislocation_rolling_v100.csv",
    index=False,
)

summary_dislocation_v100.to_csv(
    "spy_sentinel_dislocation_summary_v100.csv",
    index=False,
)

print("Extreme-dislocation research saved")
