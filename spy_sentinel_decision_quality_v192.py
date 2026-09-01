def score_taken_trade(realized_return):
    if realized_return is None:
        return None

    if realized_return >= 0.10:
        return 1.0

    if realized_return > 0:
        return 0.75

    if realized_return > -0.10:
        return 0.40

    return 0.0


def score_rejection(label):
    mapping = {
        "GOOD_ABSTENTION": 1.0,
        "NEUTRAL": 0.5,
        "MISSED_OPPORTUNITY": 0.0,
    }

    return mapping.get(label)


if __name__ == "__main__":

    tests = [
        ("trade_win", score_taken_trade(0.15), 1.0),
        ("small_win", score_taken_trade(0.03), 0.75),
        ("large_loss", score_taken_trade(-0.20), 0.0),
        ("good_reject", score_rejection("GOOD_ABSTENTION"), 1.0),
        ("missed_opportunity", score_rejection("MISSED_OPPORTUNITY"), 0.0),
    ]

    print("\nV192 DECISION QUALITY TESTS")

    all_pass = True

    for name, result, expected in tests:
        passed = result == expected
        all_pass &= passed

        print(
            name,
            "| score:", result,
            "| expected:", expected,
            "| PASS:", passed
        )

    print("\nALL TESTS PASS:", all_pass)
