import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = Path.cwd()
PYTHON = BASE.parent / ".venv" / "bin" / "python"

ET = ZoneInfo("America/New_York")
now = datetime.now(ET)

minutes = now.hour * 60 + now.minute

market_open = (
    now.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

print("\nV155 REJECTION SESSION")
print("Eastern time:", now.isoformat())
print("Regular market open:", market_open)

if not market_open:
    print("SESSION INACTIVE — MARKET CLOSED")
    print("NO REJECTION CREATED")
    raise SystemExit(0)

steps = [
    "spy_sentinel_candidate_v125.py",
    "spy_sentinel_rejection_gate_v150.py",
    "spy_sentinel_shadow_queue_v154.py",
    "spy_sentinel_learning_quality_v152.py",
]

for script in steps:
    print("\nRUNNING:", script)

    r = subprocess.run(
        [str(PYTHON), str(BASE / script)],
        cwd=str(BASE),
        text=True,
    )

    if r.returncode != 0:
        raise RuntimeError(
            f"{script} failed"
        )

print("\nCLEAN REJECTION SESSION COMPLETE")
print("NO ORDER SUBMISSION")
