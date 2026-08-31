import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

BASE = Path.cwd()

data_file = BASE / "spy_sentinel_options_features_v112.csv"

if not data_file.exists():
    raise RuntimeError("V106 feature dataset not found")

df = pd.read_csv(data_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df["date"] = df["timestamp"].dt.date

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

df["target"] = (
    df["future_return_60m"] > 0
).astype(int)

days = sorted(
    df["date"].unique()
)

print("\nV113 60-DAY LEAKAGE-SAFE OPTIONS ROLLING TEST")
print("Trading days:", len(days))
print("Rows:", len(df))
print("Features:", len(feature_cols))

# --------------------------------------------------
# STRICT EXPANDING-WINDOW TEST
# First 8 days train.
# Then test next 2 days.
# Expand forward.
# --------------------------------------------------

windows = []

train_end = 8

while train_end + 2 <= len(days):

    train_days = days[:train_end]
    test_days = days[
        train_end:train_end + 2
    ]

    windows.append({
        "train_days": train_days,
        "test_days": test_days,
    })

    train_end += 2

print("Rolling windows:", len(windows))

results = []

for i, w in enumerate(windows, start=1):

    train = df[
        df["date"].isin(
            w["train_days"]
        )
    ].copy()

    test = df[
        df["date"].isin(
            w["test_days"]
        )
    ].copy()

    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=150,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=42,
    )

    model.fit(
        train[feature_cols],
        train["target"],
    )

    prob = model.predict_proba(
        test[feature_cols]
    )[:, 1]

    pred = (
        prob >= 0.50
    ).astype(int)

    bal = (
        balanced_accuracy_score(
            test["target"],
            pred
        ) * 100
    )

    auc = (
        roc_auc_score(
            test["target"],
            prob
        ) * 100
    )

    # Higher-confidence subset
    confident = (
        (prob >= 0.55)
        | (prob <= 0.45)
    )

    conf_n = int(
        confident.sum()
    )

    if conf_n > 0:

        conf_pred = (
            prob[confident] >= 0.50
        ).astype(int)

        conf_actual = (
            test["target"]
            .to_numpy()[
                confident
            ]
        )

        conf_acc = (
            conf_pred
            == conf_actual
        ).mean() * 100

        raw_returns = (
            test["future_return_60m"]
            .to_numpy()[
                confident
            ]
        )

        signed_returns = np.where(
            conf_pred == 1,
            raw_returns,
            -raw_returns
        )

        avg_return = (
            signed_returns.mean()
            * 100
        )

    else:

        conf_acc = 0.0
        avg_return = 0.0

    results.append({
        "window": i,
        "train_days": len(
            w["train_days"]
        ),
        "test_days": len(
            w["test_days"]
        ),
        "test_rows": len(test),
        "balanced_accuracy": bal,
        "auc": auc,
        "confident_signals": conf_n,
        "confident_accuracy": conf_acc,
        "confident_avg_return": avg_return,
    })

    print(
        f"Window {i}: "
        f"bal={bal:.2f}% | "
        f"AUC={auc:.2f}% | "
        f"conf={conf_n} | "
        f"acc={conf_acc:.2f}% | "
        f"ret={avg_return:+.4f}%"
    )

res = pd.DataFrame(results)

# --------------------------------------------------
# AGGREGATE
# --------------------------------------------------

total_conf = int(
    res["confident_signals"].sum()
)

weighted_correct = (
    (
        res["confident_accuracy"]
        / 100
    )
    * res["confident_signals"]
).sum()

weighted_accuracy = (
    weighted_correct
    / total_conf
    * 100
    if total_conf
    else 0.0
)

weighted_return = (
    (
        res["confident_avg_return"]
        * res["confident_signals"]
    ).sum()
    / total_conf
    if total_conf
    else 0.0
)

positive_windows = int(
    (
        res["confident_avg_return"]
        > 0
    ).sum()
)

mean_bal = (
    res["balanced_accuracy"].mean()
)

mean_auc = (
    res["auc"].mean()
)

print("\nV113 AGGREGATE")
print("Confident signals:", total_conf)
print(
    f"Weighted accuracy: "
    f"{weighted_accuracy:.2f}%"
)
print(
    f"Weighted directional return: "
    f"{weighted_return:+.4f}%"
)
print(
    "Positive-return windows:",
    positive_windows,
    "/",
    len(res),
)
print(
    f"Mean balanced accuracy: "
    f"{mean_bal:.2f}%"
)
print(
    f"Mean AUC: "
    f"{mean_auc:.2f}%"
)

# --------------------------------------------------
# PREREGISTERED GATE
# --------------------------------------------------

PASS = (
    len(res) >= 5
    and total_conf >= 150
    and weighted_accuracy >= 54
    and weighted_return > 0
    and positive_windows >= 4
    and mean_bal >= 52
    and mean_auc >= 52
)

print("\nV113 OPTIONS EDGE GATE")
print("Pass:", PASS)

if PASS:
    print(
        "Verdict: OPTIONS FEATURES "
        "SURVIVE INITIAL ROLLING TEST"
    )
else:
    print(
        "Verdict: OPTIONS FEATURES "
        "DO NOT YET GENERALIZE"
    )

print("\nNO PAPER UNLOCK")
print("NO LIVE UNLOCK")
print("NO ORDER CODE")

res.to_csv(
    "spy_sentinel_options_rolling_v113.csv",
    index=False
)

print(
    "Saved: spy_sentinel_options_rolling_v113.csv"
)
