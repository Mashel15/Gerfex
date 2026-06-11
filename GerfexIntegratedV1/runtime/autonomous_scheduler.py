import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.goal_manager import list_goals
from runtime.goal_worker import run_next_goal
from runtime.autonomous_goal_generator import generate_and_queue

def propose_goal():
    pending = list_goals("pending")
    if pending.get("count", 0) > 0:
        return {"ok": True, "mode": "use_existing_pending"}

    generated = generate_and_queue()
    return {
        "ok": True,
        "mode": "generated_by_goal_generator",
        "generated": generated
    }

def scheduler_tick():
    proposal = propose_goal()
    worker = run_next_goal()
    return {
        "ok": True,
        "scheduler": "AUTONOMOUS_SCHEDULER_V1",
        "proposal": proposal,
        "worker": worker
    }

def run_ticks(count=1, sleep_seconds=0):
    results = []
    for _ in range(count):
        results.append(scheduler_tick())
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return {"ok": True, "ticks": count, "results": results}

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(json.dumps(run_ticks(count), ensure_ascii=False, indent=2))
