import subprocess
import time
from pathlib import Path
from datetime import datetime

BASE = Path.cwd()
python = BASE.parent / ".venv" / "bin" / "python"
candidate_script = BASE / "spy_sentinel_candidate_v125.py"

print("\nSPY SENTINEL V126 — CANDIDATE REFRESH")
print("Refresh interval: 15 seconds")
print("Press Control+C only when you want to stop it.")

while True:
    r = subprocess.run(
        [str(python), str(candidate_script)],
        cwd=str(BASE),
        capture_output=True,
        text=True,
    )

    now = datetime.now().strftime("%H:%M:%S")

    if r.returncode == 0:
        print(now, "| CANDIDATE UPDATED")
    else:
        print(now, "| CANDIDATE UPDATE ERROR")
        print(r.stderr[-500:])

    time.sleep(15)
