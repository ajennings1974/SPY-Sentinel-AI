import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = Path.home() / "SPY_SENTINEL_EVIDENCE_RUNTIME"
PYTHON = BASE / ".venv" / "bin" / "python"
SCRIPT = BASE / "spy_sentinel_paired_evidence_v201.py"

ET = ZoneInfo("America/New_York")
now = datetime.now(ET)

minutes = now.hour * 60 + now.minute

# Evidence collection only.
# Weekdays, 9:35 AM through 3:15 PM Eastern.
collection_window = (
    now.weekday() < 5
    and minutes >= 575
    and minutes <= 915
)

print("\nSPY SENTINEL V211 — BACKGROUND PAIRED EVIDENCE")
print("Eastern time:", now.isoformat())
print("Collection window active:", collection_window)

if not collection_window:
    print("PASS — OUTSIDE COLLECTION WINDOW")
    raise SystemExit(0)

if not SCRIPT.exists():
    raise RuntimeError("V201 paired collector missing")

r = subprocess.run(
    [str(PYTHON), str(SCRIPT)],
    cwd=str(BASE),
    text=True,
    capture_output=True,
)

print(r.stdout[-2500:])

if r.returncode != 0:
    print(r.stderr[-2500:])
    raise RuntimeError("V201 paired evidence run failed")

print("\nV211 CYCLE COMPLETE")
print("PAPER ORDER SUBMITTED: False")
print("LIVE ORDER SUBMITTED: False")
print("CHAMPION CHANGE AUTHORIZED: False")
