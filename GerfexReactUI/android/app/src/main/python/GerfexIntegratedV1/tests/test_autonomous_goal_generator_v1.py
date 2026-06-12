import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.autonomous_goal_generator import generate_goal

r = generate_goal()
assert r["ok"]
assert "mode" in r
print("AUTONOMOUS GOAL GENERATOR V1 OK")
