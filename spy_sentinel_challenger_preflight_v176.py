import json
from pathlib import Path

BASE = Path.cwd()

gate_file = BASE / "spy_sentinel_challenger_gate_v158.json"
contract_file = BASE / "spy_sentinel_feature_contract_v159.json"
promotion_file = BASE / "spy_sentinel_promotion_contract_v160.json"

required = [
    gate_file,
    contract_file,
    promotion_file,
]

missing = [
    p.name for p in required
    if not p.exists()
]

if missing:
    raise RuntimeError(
        "Missing required governance files: "
        + ", ".join(missing)
    )

gate = json.loads(gate_file.read_text())
contract = json.loads(contract_file.read_text())
promotion = json.loads(promotion_file.read_text())

result = {
    "training_eligible":
        gate["challenger_training_eligible"],

    "clean_episode_count":
        gate["current"]["total"],

    "accepted_count":
        gate["current"]["accepted"],

    "rejected_count":
        gate["current"]["rejected"],

    "feature_contract_loaded":
        True,

    "promotion_contract_loaded":
        True,

    "automatic_promotion":
        promotion["automatic_self_promotion"],

    "live_trading_enabled":
        promotion["live_trading_enabled"],
}

out = BASE / "spy_sentinel_challenger_preflight_v176.json"

out.write_text(
    json.dumps(result, indent=2)
)

print("\nV176 CHALLENGER PREFLIGHT")
for k, v in result.items():
    print(k + ":", v)

if not result["training_eligible"]:
    print("\nTRAINING BLOCKED — INSUFFICIENT CLEAN EXPERIENCE")
else:
    print("\nTRAINING MAY PROCEED IN SHADOW MODE ONLY")

print("\nNO ORDER SUBMISSION")
print("NO CHAMPION REPLACEMENT")
