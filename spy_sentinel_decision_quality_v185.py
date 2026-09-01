import json
from pathlib import Path

BASE = Path.cwd()

def score_trade(pnl_pct, exit_reason):
    if pnl_pct is None:
        return 0.0, "UNKNOWN"

    pnl_pct = float(pnl_pct)

    if pnl_pct > 0:
        return min(1.0, 0.5 + pnl_pct), "GOOD_TRADE"

    if exit_reason == "STOP_LOSS":
        return max(0.0, 0.5 + pnl_pct), "BAD_TRADE_STOPPED"

    return max(0.0, 0.5 + pnl_pct), "BAD_TRADE"


def score_rejection(label):
    mapping = {
        "GOOD_ABSTENTION": (1.0, "GOOD_NO_TRADE"),
        "MISSED_OPPORTUNITY": (0.0, "BAD_NO_TRADE"),
        "NEUTRAL": (0.5, "NEUTRAL_NO_TRADE"),
        "PENDING": (None, "PENDING"),
    }

    return mapping.get(
        label,
        (None, "UNKNOWN")
    )


tests = [
    ("trade_win", score_trade(0.12, "PROFIT_TARGET")),
    ("trade_loss", score_trade(-0.15, "STOP_LOSS")),
    ("reject_good", score_rejection("GOOD_ABSTENTION")),
    ("reject_bad", score_rejection("MISSED_OPPORTUNITY")),
]

print("\nV185 DECISION QUALITY SCORER")

for name, result in tests:
    print(name, "=>", result)

print("\nNO ORDER SUBMISSION")
print("NO MODEL TRAINING")
