import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

REGISTRY = BASE / "spy_sentinel_decision_registry_v149.jsonl"

def register_decision(
    action,
    symbol=None,
    reasons=None,
    candidate_snapshot=None,
):
    decision_id = "decision-" + uuid.uuid4().hex[:12]

    record = {
        "decision_id": decision_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "symbol": symbol,
        "reasons": reasons or [],
        "candidate_snapshot": candidate_snapshot or {},
        "paper_order_submitted": False,
        "live_order_submitted": False,
        "counterfactual_status": (
            "PENDING"
            if action == "NO_TRADE"
            else "NOT_APPLICABLE"
        ),
        "eligible_for_learning": True,
        "champion_changed": False,
    }

    with REGISTRY.open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")

    return record


if __name__ == "__main__":
    demo = register_decision(
        action="TEST_ONLY",
        reasons=["PIPELINE_TEST"],
    )

    print("\nV149 DECISION REGISTRY")
    print("Decision ID:", demo["decision_id"])
    print("Action:", demo["action"])
    print("Saved:", REGISTRY.name)
    print("NO ORDER SUBMITTED")
