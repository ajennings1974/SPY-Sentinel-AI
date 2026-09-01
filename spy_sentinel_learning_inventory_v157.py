import json
from pathlib import Path

BASE = Path.cwd()

def read_jsonl(name):
    p = BASE / name

    if not p.exists():
        return []

    rows = []

    for line in p.read_text().splitlines():
        if not line.strip():
            continue

        try:
            rows.append(json.loads(line))
        except Exception:
            pass

    return rows

accepted = read_jsonl(
    "spy_sentinel_experience_log_v135.jsonl"
)

rejected_clean = read_jsonl(
    "spy_sentinel_rejection_learning_clean_v146b.jsonl"
)

rejected_fresh = read_jsonl(
    "spy_sentinel_rejections_v147b.jsonl"
)

quarantined = read_jsonl(
    "spy_sentinel_rejection_quarantine_v146b.jsonl"
)

inventory = {
    "accepted_episodes":
        len(accepted),

    "clean_rejected_episodes":
        len(rejected_clean) + len(rejected_fresh),

    "quarantined_episodes":
        len(quarantined),

    "total_clean_learning_episodes":
        len(accepted)
        + len(rejected_clean)
        + len(rejected_fresh),

    "quarantined_data_allowed":
        False,
}

out = BASE / "spy_sentinel_learning_inventory_v157.json"

out.write_text(
    json.dumps(
        inventory,
        indent=2
    )
)

print("\nV157 LEARNING INVENTORY")

for k, v in inventory.items():
    print(k + ":", v)

print("Saved:", out.name)
