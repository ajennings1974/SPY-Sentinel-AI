import json
from pathlib import Path
from collections import Counter

BASE = Path.cwd()

registry = BASE / "spy_sentinel_decision_registry_v149.jsonl"

rows = []

if registry.exists():
    for line in registry.read_text().splitlines():
        if not line.strip():
            continue

        try:
            rows.append(json.loads(line))
        except Exception:
            pass

decision_ids = [
    x.get("decision_id")
    for x in rows
    if x.get("decision_id")
]

candidate_keys = [
    x.get("candidate_key")
    for x in rows
    if x.get("candidate_key")
]

id_counts = Counter(decision_ids)
key_counts = Counter(candidate_keys)

duplicate_ids = {
    k: v for k, v in id_counts.items()
    if v > 1
}

duplicate_keys = {
    k: v for k, v in key_counts.items()
    if v > 1
}

result = {
    "registry_rows": len(rows),
    "duplicate_decision_ids": duplicate_ids,
    "duplicate_candidate_keys": duplicate_keys,
    "dedup_pass": (
        not duplicate_ids
        and not duplicate_keys
    ),
}

out = BASE / "spy_sentinel_dedup_v168.json"

out.write_text(
    json.dumps(
        result,
        indent=2
    )
)

print("\nV168 DEDUP AUDIT")
print("Registry rows:", len(rows))
print("Duplicate IDs:", duplicate_ids)
print("Duplicate candidate keys:", duplicate_keys)
print("DEDUP PASS:", result["dedup_pass"])
