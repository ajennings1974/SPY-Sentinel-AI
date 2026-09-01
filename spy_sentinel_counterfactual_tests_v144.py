def classify(entry, current):
    ret = current / entry - 1

    if ret >= 0.05:
        return "MISSED_OPPORTUNITY", ret

    if ret <= -0.05:
        return "GOOD_ABSTENTION", ret

    return "NEUTRAL", ret


tests = [
    ("rejected_then_up", 1.00, 1.10, "MISSED_OPPORTUNITY"),
    ("rejected_then_down", 1.00, 0.90, "GOOD_ABSTENTION"),
    ("rejected_flat", 1.00, 1.01, "NEUTRAL"),
]

print("\nV144 COUNTERFACTUAL TESTS")

all_pass = True

for name, entry, current, expected in tests:
    result, ret = classify(entry, current)
    passed = result == expected
    all_pass &= passed

    print(
        name,
        "| result:", result,
        "| return:", round(ret * 100, 2), "%",
        "| PASS:", passed
    )

print("\nALL COUNTERFACTUAL TESTS PASS:", all_pass)
print("NO ORDER CODE")
