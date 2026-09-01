import json
from pathlib import Path

BASE = Path.cwd()

def count_lines(name):
    p = BASE / name

    if not p.exists():
        return 0

    return len([
        x
        for x in p.read_text().splitlines()
        if x.strip()
    ])

data = {
    "accepted_learning_episodes":
        count_lines(
            "spy_sentinel_experience_log_v135.jsonl"
        ),

    "clean_rejection_episodes":
        count_lines(
            "spy_sentinel_rejection_learning_clean_v146b.jsonl"
        ),

    "quarantined_rejection_episodes":
        count_lines(
            "spy_sentinel_rejection_quarantine_v146b.jsonl"
        ),

    "registered_decisions":
        count_lines(
            "spy_sentinel_decision_registry_v149.jsonl"
        ),

    "quarantined_data_can_train":
        False,

    "automatic_champion_promotion":
        False,
}

out = BASE / "spy_sentinel_learning_quality_v152.json"

out.write_text(
    json.dumps(
        data,
        indent=2
    )
)

print("\nV152 LEARNING QUALITY")
for k, v in data.items():
    print(k + ":", v)

print("Saved:", out.name)
