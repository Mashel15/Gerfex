import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.goal_manager import add_goal, list_goals, next_goal, complete_goal

r = add_goal("افتح كروم", source="test")
assert r["ok"]

p = list_goals("pending")
assert p["count"] >= 1

n = next_goal()
assert n["ok"]
gid = n["goal"]["id"]

c = complete_goal(gid, {"ok": True})
assert c["ok"]
assert c["goal"]["status"] == "completed"

print("GOAL QUEUE MANAGER V1 OK")
