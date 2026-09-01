import subprocess
from pathlib import Path

BASE = Path.cwd()
PYTHON = (
    BASE.parent
    / ".venv"
    / "bin"
    / "python"
)

scripts = [
    "spy_sentinel_market_evidence_v181.py",
    "spy_sentinel_decision_logger_v182.py",
    "spy_sentinel_decision_dedup_v183.py",
    "spy_sentinel_evidence_summary_v184.py",
]

print("\nV185 MARKET EVIDENCE SESSION")

for script in scripts:
    print("\nRUNNING:", script)

    r = subprocess.run(
        [
            str(PYTHON),
            str(BASE / script),
        ],
        cwd=str(BASE),
        text=True,
    )

    if r.returncode != 0:
        raise RuntimeError(
            script + " failed"
        )

print("\nV185 SESSION COMPLETE")
print("NO ORDER SUBMISSION")
print("NO CHAMPION CHANGE")
