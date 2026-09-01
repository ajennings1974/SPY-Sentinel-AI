import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

gate = json.load(
    open(
        BASE
        / "spy_sentinel_challenger_gate_v158.json"
    )
)

status = {
    "generated_utc":
        datetime.now(timezone.utc).isoformat(),

    "champion":
        "SPY_SENTINEL_CHAMPION_V1",

    "challenger":
        "NOT YET TRAINED",

    "training_eligible":
        gate["challenger_training_eligible"],

    "clean_episode_count":
        gate["current"]["total"],

    "accepted_trade_count":
        gate["current"]["accepted"],

    "rejected_episode_count":
        gate["current"]["rejected"],

    "champion_changed":
        False,

    "reason":
        (
            "ENOUGH CLEAN EXPERIENCE"
            if gate["challenger_training_eligible"]
            else
            "COLLECTING CLEAN EXPERIENCE"
        ),
}

out = BASE / "spy_sentinel_challenger_status_v161.json"

out.write_text(
    json.dumps(
        status,
        indent=2
    )
)

print("\nV161 CHALLENGER STATUS")
print("Champion:", status["champion"])
print("Challenger:", status["challenger"])
print("Training eligible:", status["training_eligible"])
print("Clean episodes:", status["clean_episode_count"])
print("Status:", status["reason"])
print("Champion changed:", status["champion_changed"])
