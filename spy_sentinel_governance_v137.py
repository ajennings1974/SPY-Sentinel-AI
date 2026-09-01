import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

experience_log = BASE / "spy_sentinel_experience_log_v135.jsonl"

episodes = []

if experience_log.exists():
    for line in experience_log.read_text().splitlines():
        if line.strip():
            try:
                episodes.append(json.loads(line))
            except Exception:
                pass

episode_count = len(episodes)

governance = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),

    "architecture": {
        "champion": "SPY_SENTINEL_CHAMPION_V1",
        "challenger": "NOT YET TRAINED",
        "automatic_retraining": False,
        "automatic_promotion": False,
    },

    "current_learning_state": {
        "experience_episodes": episode_count,
        "minimum_experience_episodes_for_challenger": 20,
        "challenger_training_eligible": episode_count >= 20,
    },

    "promotion_gates": {
        "no_data_leakage": True,
        "rolling_out_of_sample_required": True,
        "fresh_paper_validation_required": True,
        "transaction_costs_required": True,
        "risk_and_drawdown_review_required": True,
        "reproducibility_required": True,
        "challenger_must_beat_champion": True,
    },

    "promotion_policy": {
        "rule_1": "A Challenger may learn from completed experiences.",
        "rule_2": "A Challenger may never promote itself.",
        "rule_3": "Historical improvement alone is insufficient.",
        "rule_4": "The Challenger must survive rolling out-of-sample testing.",
        "rule_5": "The Challenger must then survive fresh paper validation.",
        "rule_6": "Risk-adjusted performance must improve without unacceptable drawdown.",
        "rule_7": "Only after every promotion gate passes may the Challenger replace the Champion.",
    },

    "status": (
        "CHALLENGER TRAINING ELIGIBLE"
        if episode_count >= 20
        else "COLLECTING EXPERIENCE"
    ),

    "champion_changed": False,
}

out = BASE / "spy_sentinel_governance_v137.json"

out.write_text(
    json.dumps(
        governance,
        indent=2
    )
)

print("\nSPY SENTINEL V137 — CHAMPION / CHALLENGER GOVERNANCE")
print("Experience episodes:", episode_count)
print(
    "Minimum before Challenger training:",
    governance["current_learning_state"]["minimum_experience_episodes_for_challenger"]
)
print(
    "Challenger training eligible:",
    governance["current_learning_state"]["challenger_training_eligible"]
)
print("Champion:", governance["architecture"]["champion"])
print("Challenger:", governance["architecture"]["challenger"])
print("Champion changed:", governance["champion_changed"])
print("Status:", governance["status"])
print("Saved:", out.name)

print("\nSAFETY")
print("AUTOMATIC RETRAINING: DISABLED")
print("AUTOMATIC PROMOTION: DISABLED")
print("LIVE TRADING: DISABLED")
