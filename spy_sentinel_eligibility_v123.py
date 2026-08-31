import json
from pathlib import Path

BASE = Path.cwd()

state_file = BASE / "spy_sentinel_live_state_v120.json"

if not state_file.exists():
    raise RuntimeError("Live state file not found")

state = json.loads(state_file.read_text())

open_positions = state.get("open_positions", 0)

validated_edge = False
live_authorized = False
paper_only = True
max_contracts = 1
max_demo_cost = 250
account_clear = (open_positions == 0)

gates = [
    {
        "name": "Paper environment",
        "passed": paper_only,
        "status": "PASS" if paper_only else "FAIL",
        "why": "All execution is confined to Alpaca paper trading."
    },
    {
        "name": "Account clear",
        "passed": account_clear,
        "status": "PASS" if account_clear else "FAIL",
        "why": "Only one controlled paper position may exist at a time."
    },
    {
        "name": "Maximum contracts",
        "passed": True,
        "status": "PASS",
        "why": f"Maximum quantity remains {max_contracts} contract."
    },
    {
        "name": "Maximum demo cost",
        "passed": True,
        "status": "PASS",
        "why": f"Demo exposure is capped at ${max_demo_cost}."
    },
    {
        "name": "Validated profitability edge",
        "passed": validated_edge,
        "status": "PASS" if validated_edge else "FAIL",
        "why": "Research has not yet demonstrated a repeatable profitable edge."
    },
    {
        "name": "Live-money authorization",
        "passed": live_authorized,
        "status": "PASS" if live_authorized else "DISABLED",
        "why": "Live-money trading is intentionally unavailable."
    },
]

paper_demo_eligible = (
    paper_only
    and account_clear
)

validated_strategy_eligible = (
    paper_demo_eligible
    and validated_edge
)

live_eligible = False

what_must_change = []

if not account_clear:
    what_must_change.append(
        "Existing paper position must be closed before another demo entry."
    )

if not validated_edge:
    what_must_change.append(
        "The validation gate must prove a repeatable edge before the strategy can be promoted beyond controlled demo status."
    )

what_must_change.append(
    "Live-money authorization remains disabled regardless of demo eligibility."
)

result = {
    "paper_demo_eligible": paper_demo_eligible,
    "validated_strategy_eligible": validated_strategy_eligible,
    "live_eligible": live_eligible,
    "gates": gates,
    "what_must_change": what_must_change,
}

Path(
    "spy_sentinel_eligibility_v123.json"
).write_text(
    json.dumps(
        result,
        indent=2
    )
)

print("\nV123 ELIGIBILITY ENGINE")
print("Paper-demo eligible:", paper_demo_eligible)
print("Validated-strategy eligible:", validated_strategy_eligible)
print("Live eligible:", live_eligible)
print("Saved: spy_sentinel_eligibility_v123.json")
