import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.cwd()

OUT = BASE / "spy_sentinel_session_decisions_v163.jsonl"

def create_decision(
    action,
    symbol,
    candidate_snapshot,
    reasons=None,
):
    decision_id = "session-" + uuid.uuid4().hex[:12]

    x = {
        "decision_id": decision_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "symbol": symbol,
        "candidate_snapshot": candidate_snapshot,
        "reasons": reasons or [],
        "counterfactual_required": action == "NO_TRADE",
        "lifecycle_required": action == "TRADE",
        "champion_changed": False,
        "automatic_model_change": False,
    }

    with OUT.open("a") as f:
        f.write(json.dumps(x, default=str) + "\n")

    return x


if __name__ == "__main__":

    x = create_decision(
        action="TEST_ONLY",
        symbol=None,
        candidate_snapshot={},
        reasons=["PIPELINE_TEST"],
    )

    print("\nV163 SESSION DECISION")
    print("Decision ID:", x["decision_id"])
    print("Action:", x["action"])
    print("Champion changed:", x["champion_changed"])
    print("NO ORDER SUBMITTED")
