import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

BASE = Path.cwd()

decision_file = BASE / "spy_sentinel_session_decisions_v163.jsonl"
shadow_file = BASE / "spy_sentinel_shadow_schedule_v165.json"

actions = Counter()
reasons = Counter()

if decision_file.exists():
    for line in decision_file.read_text().splitlines():

        if not line.strip():
            continue

        x = json.loads(line)

        if x.get("action") == "TEST_ONLY":
            continue

        actions[x.get("action")] += 1

        for reason in x.get("reasons", []):
            reasons[reason] += 1

shadow = {
    "episodes": []
}

if shadow_file.exists():
    shadow = json.loads(
        shadow_file.read_text()
    )

summary = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "trades":
        actions.get("TRADE", 0),

    "no_trade_decisions":
        actions.get("NO_TRADE", 0),

    "pending_counterfactuals":
        len([
            x
            for x in shadow.get("episodes", [])
            if x.get("status") == "PENDING"
        ]),

    "top_rejection_reasons":
        dict(reasons),

    "champion_changed":
        False,

    "automatic_retraining":
        False,

    "live_trading":
        False,
}

out = BASE / "spy_sentinel_session_summary_v166.json"

out.write_text(
    json.dumps(
        summary,
        indent=2
    )
)

print("\nV166 SESSION SUMMARY")
print("Trades:", summary["trades"])
print("NO TRADE:", summary["no_trade_decisions"])
print("Pending counterfactuals:", summary["pending_counterfactuals"])
print("Champion changed:", summary["champion_changed"])
print("Automatic retraining:", summary["automatic_retraining"])
print("Live trading:", summary["live_trading"])
print("Saved:", out.name)
