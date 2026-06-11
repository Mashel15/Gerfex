import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.autonomous_scheduler import propose_goal

r = propose_goal()
assert r["ok"]

print("AUTONOMOUS SCHEDULER V1 OK")
