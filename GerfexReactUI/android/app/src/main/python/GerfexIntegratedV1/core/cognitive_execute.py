import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.perception_cycle import run_perception_cycle
from search_bundle.core.action_builder import build_actions
from core.execution_manager import execute

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
        "note": "Execution bundle built. execute_cognitive_goal may execute executable actions."
    }


def execute_cognitive_goal(goal):
    bundle_result = build_execution_bundle(goal)
    actions = bundle_result.get("executable_actions", [])

    if not actions:
        return {
            "ok": False,
            "mode": "cognitive_execute",
            "reason": "no_executable_actions",
            "goal": goal,
            "bundle_result": bundle_result
        }

    decision = {
        "ok": True,
        "brain": "CognitiveExecute",
        "intent": bundle_result.get("bundle", {}).get("intent", "cognitive_action"),
        "target": bundle_result.get("bundle", {}).get("query") or "android",
        "actions": [
            {"action": a.get("action"), "args": a.get("args", {})}
            for a in actions
        ],
        "reason": "perception_plan_action_bundle"
    }

    execution = execute(decision)

    return {
        "ok": execution.get("ok", False),
        "mode": "cognitive_execute",
        "goal": goal,
        "decision": decision,
        "execution": execution,
        "bundle_result": bundle_result
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
