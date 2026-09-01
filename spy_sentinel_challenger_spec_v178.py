import json
from pathlib import Path

BASE = Path.cwd()

spec = {
    "challenger_id":
        "SPY_SENTINEL_CHALLENGER_V1",

    "training_mode":
        "SHADOW ONLY",

    "allowed_learning_sources": [
        "clean accepted trade episodes",
        "clean rejected trade episodes",
        "counterfactual outcomes",
    ],

    "forbidden_learning_sources": [
        "quarantined episodes",
        "future information",
        "stale candidate snapshots",
        "post-decision labels used as decision-time features",
    ],

    "training_targets": [
        "probability trade is favorable",
        "probability abstention is favorable",
        "expected return after estimated costs",
    ],

    "execution_authority":
        False,

    "self_promotion_authority":
        False,

    "independent_validation_required":
        True,
}

out = BASE / "spy_sentinel_challenger_spec_v178.json"

out.write_text(
    json.dumps(spec, indent=2)
)

print("\nV178 CHALLENGER SPEC")
print("Challenger:", spec["challenger_id"])
print("Mode:", spec["training_mode"])
print("Execution authority:", spec["execution_authority"])
print("Self-promotion:", spec["self_promotion_authority"])
