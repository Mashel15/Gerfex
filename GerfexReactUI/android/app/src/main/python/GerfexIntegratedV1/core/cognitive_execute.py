import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.perception_cycle import run_perception_cycle
from planner.action_builder import build_actions

def build_execution_bundle(goal):
    perception = run_perception_cycle(goal)

    plan = perception.get("plan", {})

    bundle = build_actions(
        goal,
        plan,
        perception.get("understanding", {})
    )

    executable = [
        x for x in bundle.get("action_bundle", [])
        if x.get("executable")
    ]

    return {
        "ok": True,
        "goal": goal,
        "perception": perception,
        "bundle": bundle,
        "executable_actions": executable,
        "note": "Execution preview only. No actions executed."
    }

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "ابحث عن أخبار الذكاء الاصطناعي"

    print(
        json.dumps(
            build_execution_bundle(goal),
            ensure_ascii=False,
            indent=2
        )
    )
