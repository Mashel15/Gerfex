import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.goal_manager import next_goal, complete_goal, fail_goal, list_goals
from core.gerfex_core import run_goal

def run_next_goal():
    n = next_goal()
    if not n.get("ok"):
        return {"ok": False, "reason": "no_pending_goals"}

    item = n["goal"]
    gid = item["id"]
    goal = item["goal"]

    try:
        result = run_goal(goal)
        if result.get("ok"):
            done = complete_goal(gid, result)
            return {"ok": True, "goal_id": gid, "goal": goal, "result": result, "queue_update": done}
        else:
            failed = fail_goal(gid, result)
            return {"ok": False, "goal_id": gid, "goal": goal, "result": result, "queue_update": failed}
    except Exception as e:
        failed = fail_goal(gid, {"error": str(e)})
        return {"ok": False, "goal_id": gid, "goal": goal, "error": str(e), "queue_update": failed}

def run_all_pending(limit=10):
    results = []
    for _ in range(limit):
        pending = list_goals("pending")
        if pending.get("count", 0) <= 0:
            break
        results.append(run_next_goal())
    return {"ok": True, "processed": len(results), "results": results}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "next"
    if mode == "all":
        print(json.dumps(run_all_pending(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(run_next_goal(), ensure_ascii=False, indent=2))
