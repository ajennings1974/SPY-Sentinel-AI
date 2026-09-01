import json
from pathlib import Path

from spy_sentinel_decision_quality_v185 import (
    score_trade,
    score_rejection,
)

BASE = Path.cwd()

src = BASE / "spy_sentinel_clean_episodes_v186.json"

data = json.loads(
    src.read_text()
)

scored = []

for x in data["episodes"]:

    if x["episode_type"] == "ACCEPTED_TRADE":

        trade = x.get("trade", {})

        score, label = score_trade(
            trade.get("realized_pnl_pct"),
            trade.get("exit_reason"),
        )

    else:

        result = (
            x.get("labels", {})
            .get("counterfactual_result")
        )

        score, label = score_rejection(
            result or "PENDING"
        )

    y = dict(x)

    y["decision_quality_score"] = score
    y["decision_quality_label"] = label

    scored.append(y)


out = BASE / "spy_sentinel_episode_scores_v187.json"

out.write_text(
    json.dumps(
        {
            "episodes": scored,
            "count": len(scored),
        },
        indent=2,
        default=str,
    )
)

print("\nV187 EPISODE SCORES")

for x in scored:
    print(
        x["episode_type"],
        "| score:",
        x["decision_quality_score"],
        "| label:",
        x["decision_quality_label"],
    )

print("Saved:", out.name)
