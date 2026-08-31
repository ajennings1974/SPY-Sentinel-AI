import subprocess
import time
from pathlib import Path
from datetime import datetime

BASE = Path.cwd()

python = (
    BASE.parent
    / ".venv"
    / "bin"
    / "python"
)

state_script = (
    BASE
    / "spy_sentinel_live_state_v120.py"
)

INTERVAL_SECONDS = 15

print("\nSPY SENTINEL V122 — LIVE STATE REFRESH")
print("Refresh interval:", INTERVAL_SECONDS, "seconds")
print("Press Control+C only when you want to stop it.")

while True:

    result = subprocess.run(
        [
            str(python),
            str(state_script),
        ],
        cwd=str(BASE),
        capture_output=True,
        text=True,
    )

    now = datetime.now().strftime(
        "%H:%M:%S"
    )

    if result.returncode == 0:
        print(
            now,
            "| LIVE STATE UPDATED"
        )
    else:
        print(
            now,
            "| UPDATE ERROR"
        )
        print(
            result.stderr[-500:]
        )

    time.sleep(
        INTERVAL_SECONDS
    )
