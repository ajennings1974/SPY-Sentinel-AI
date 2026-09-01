def classify_counterfactual(return_pct):
    if return_pct <= -0.05:
        return "GOOD_ABSTENTION"

    if return_pct >= 0.05:
        return "MISSED_OPPORTUNITY"

    return "NEUTRAL"


if __name__ == "__main__":
    tests = [
        (-0.12, "GOOD_ABSTENTION"),
        (0.10, "MISSED_OPPORTUNITY"),
        (0.01, "NEUTRAL"),
    ]

    print("\nV153 REJECTION CLASSIFIER")

    all_pass = True

    for value, expected in tests:
        result = classify_counterfactual(value)
        passed = result == expected
        all_pass &= passed

        print(
            value,
            "| expected:", expected,
            "| result:", result,
            "| PASS:", passed
        )

    print("\nALL TESTS PASS:", all_pass)
