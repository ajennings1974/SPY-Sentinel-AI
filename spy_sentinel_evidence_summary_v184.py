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

actions = Counter(
    x.get("action")
    for x in rows
)

reasons = Counter()

for x in rows:
    for r in x.get("reasons", []):
        reasons[r] += 1

summary = {
    "total_clean_decisions":
        len(rows),

    "paper_ready":
        actions.get(
            "PAPER_READY",
            0
        ),

    "no_trade":
        actions.get(
            "NO_TRADE",
            0
        ),

    "top_reasons":
        dict(reasons),

    "champion_changed":
        False,

    "live_trading_enabled":
        False,
}

out = BASE / "spy_sentinel_evidence_summary_v184.json"

out.write_text(
    json.dumps(
        summary,
        indent=2
    )
)

print("\nV184 EVIDENCE SUMMARY")
print("Clean decisions:", summary["total_clean_decisions"])
print("Paper-ready:", summary["paper_ready"])
print("NO TRADE:", summary["no_trade"])
print("Top reasons:", summary["top_reasons"])
print("Champion changed:", summary["champion_changed"])
print("Saved:", out.name)
