import json
from pathlib import Path

BASE = Path.cwd()

inventory = json.load(
    open(
        BASE
        / "spy_sentinel_learning_inventory_v157.json"
    )
)

MIN_TOTAL_EPISODES = 20
MIN_ACCEPTED_TRADES = 8
MIN_REJECTED_EPISODES = 8

accepted = inventory["accepted_episodes"]
rejected = inventory["clean_rejected_episodes"]
total = inventory["total_clean_learning_episodes"]

gates = {
    "minimum_total":
        total >= MIN_TOTAL_EPISODES,

    "minimum_accepted":
        accepted >= MIN_ACCEPTED_TRADES,

    "minimum_rejected":
        rejected >= MIN_REJECTED_EPISODES,

    "quarantine_clean":
        inventory["quarantined_data_allowed"] is False,
}

eligible = all(gates.values())

result = {
    "requirements": {
        "minimum_total_episodes":
            MIN_TOTAL_EPISODES,

        "minimum_accepted_trades":
            MIN_ACCEPTED_TRADES,

        "minimum_rejected_episodes":
            MIN_REJECTED_EPISODES,
    },

    "current": {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
    },

    "gates": gates,

    "challenger_training_eligible":
        eligible,

    "champion_changed":
        False,
}

out = BASE / "spy_sentinel_challenger_gate_v158.json"

out.write_text(
    json.dumps(
        result,
        indent=2
    )
)

print("\nV158 CHALLENGER EVIDENCE GATE")
print("Clean episodes:", total)
print("Accepted trades:", accepted)
print("Rejected episodes:", rejected)

for k, v in gates.items():
    print(k, ":", v)

print(
    "CHALLENGER TRAINING ELIGIBLE:",
    eligible
)

print("CHAMPION CHANGED: False")
