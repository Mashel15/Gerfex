import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.goal_manager import add_goal
from runtime.goal_worker import run_next_goal

r = add_goal("افتح كروم", source="worker_test")
assert r["ok"]

w = run_next_goal()
assert "ok" in w
assert w.get("goal") == "افتح كروم"

print("GOAL WORKER V1 OK")
