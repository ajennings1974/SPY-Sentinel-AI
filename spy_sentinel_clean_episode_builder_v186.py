import json
from pathlib import Path

BASE = Path.cwd()

accepted_file = BASE / "spy_sentinel_learning_episode_v136.json"
rejection_file = BASE / "spy_sentinel_rejection_learning_clean_v146b.jsonl"
fresh_rejection_file = BASE / "spy_sentinel_rejections_v147b.jsonl"

episodes = []

if accepted_file.exists():
    try:
        x = json.loads(
            accepted_file.read_text()
        )

        episodes.append({
            "episode_type": "ACCEPTED_TRADE",
            "decision_id": x.get("decision_id"),
            "features": x.get("market_context", {}),
            "trade": x.get("trade", {}),
            "labels": x.get("labels", {}),
        })

    except Exception:
        pass


def load_jsonl(path):
    rows = []

    if not path.exists():
        return rows

    for line in path.read_text().splitlines():
        if not line.strip():
            continue

        try:
            rows.append(json.loads(line))
        except Exception:
            pass

    return rows


for x in load_jsonl(rejection_file):
    episodes.append({
        "episode_type": "REJECTED_CANDIDATE",
        "decision_id": x.get("decision_id"),
        "features": {
            "symbol": x.get("symbol"),
            "bid": x.get("bid"),
            "ask": x.get("ask"),
            "spread_pct": x.get("spread_pct"),
            "shadow_entry_price": x.get("shadow_entry_price"),
        },
        "labels": {
            "counterfactual_result":
                x.get("counterfactual_result"),
        },
    })


for x in load_jsonl(fresh_rejection_file):
    episodes.append({
        "episode_type": "REJECTED_CANDIDATE",
        "decision_id": x.get("decision_id"),
        "features": {
            "symbol": x.get("symbol"),
            "bid": x.get("bid"),
            "ask": x.get("ask"),
            "spread_pct": x.get("spread_pct"),
            "shadow_entry_price": x.get("shadow_entry_price"),
        },
        "labels": {
            "counterfactual_result":
                x.get("counterfactual_status"),
        },
    })


out = BASE / "spy_sentinel_clean_episodes_v186.json"

out.write_text(
    json.dumps(
        {
            "episodes": episodes,
            "count": len(episodes),
        },
        indent=2,
        default=str,
    )
)

print("\nV186 CLEAN EPISODE BUILDER")
print("Clean episodes:", len(episodes))

for x in episodes:
    print(
        x["episode_type"],
        "|",
        x.get("decision_id")
    )

print("Saved:", out.name)
