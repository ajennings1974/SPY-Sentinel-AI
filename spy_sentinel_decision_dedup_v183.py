import json
from pathlib import Path
from collections import Counter

BASE = Path.cwd()

registry = BASE / "spy_sentinel_clean_decisions_v182.jsonl"

rows = []

if registry.exists():
    for line in registry.read_text().splitlines():
        if line.strip():
            rows.append(
                json.loads(line)
            )

keys = []

for x in rows:
    keys.append(
        (
            x.get("symbol"),
            x.get("action"),
            x.get("timestamp_utc", "")[:16],
        )
    )

counts = Counter(keys)

duplicates = {
    str(k): v
    for k, v in counts.items()
    if v > 1
}

print("\nV183 DECISION DEDUP")
print("Total clean decisions:", len(rows))
print("Duplicate keys:", len(duplicates))
print("Duplicates:", duplicates)
