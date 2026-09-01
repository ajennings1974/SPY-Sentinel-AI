PROFIT_TARGET = 0.20
STOP_LOSS = -0.15
MAX_HOLD_MINUTES = 45

def exit_decision(pl_pct, hold_minutes):
    if pl_pct >= PROFIT_TARGET:
        return "PROFIT_TARGET"

    if pl_pct <= STOP_LOSS:
        return "STOP_LOSS"

    if hold_minutes >= MAX_HOLD_MINUTES:
        return "TIME_EXIT"

    return "HOLD"


tests = [
    {
        "name": "profit_target_test",
        "pl_pct": 0.25,
        "hold_minutes": 10,
        "expected": "PROFIT_TARGET",
    },
    {
        "name": "stop_loss_test",
        "pl_pct": -0.20,
        "hold_minutes": 12,
        "expected": "STOP_LOSS",
    },
    {
        "name": "time_exit_test",
        "pl_pct": 0.03,
        "hold_minutes": 50,
        "expected": "TIME_EXIT",
    },
]

print("\nSPY SENTINEL V134 — EXIT BRANCH TESTS")

all_pass = True

for t in tests:
    result = exit_decision(
        t["pl_pct"],
        t["hold_minutes"],
    )

    passed = result == t["expected"]

    print(
        t["name"],
        "| expected:", t["expected"],
        "| result:", result,
        "| PASS:", passed,
    )

    all_pass = all_pass and passed

print("\nALL EXIT BRANCHES PASS:", all_pass)

print("\nSAFETY")
print("NO ALPACA ORDER SUBMISSION")
print("NO PAPER ORDER")
print("NO LIVE ORDER")
