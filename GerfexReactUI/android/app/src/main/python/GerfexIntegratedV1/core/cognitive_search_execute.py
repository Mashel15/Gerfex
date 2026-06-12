import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from context.context_manager import prepare_context
from observation.screen_observer import observe
from understanding.screen_understanding import understand_screen
from planner.action_planner import create_plan
from planner.action_builder import build_actions
from planner.target_resolver import resolve_targets
from android.android_bridge import queue_action

SUPPORTED_ACTIONS = {
    "open_url",
    "tap",
    "type_text",
    "press_enter",
    "wait"
}

def execute_goal(goal):
    context_result = prepare_context(goal)

    time.sleep(4)

    obs = observe()
    understanding = understand_screen()
    plan = create_plan(goal, understanding)
    bundle = build_actions(goal, plan, understanding)

    resolved = resolve_targets(obs, bundle)

    queued = []

    for action in resolved.get("resolved_actions", []):
        name = action.get("action")

        if name not in SUPPORTED_ACTIONS:
            continue

        queued.append(
            queue_action({
                "action": name,
                "args": action.get("args", {})
            })
        )

    return {
        "ok": True,
        "version": "COGNITIVE_SEARCH_EXECUTE_V3",
        "goal": goal,
        "context": context_result,
        "observation": {
            "top_package": obs.get("top_package"),
            "item_count": obs.get("item_count"),
            "clickable_count": obs.get("clickable_count")
        },
        "understanding": {
            "screen_type": understanding.get("screen_type"),
            "summary": understanding.get("summary"),
            "confidence": understanding.get("confidence")
        },
        "plan": plan,
        "bundle": bundle,
        "resolved": resolved,
        "queued_count": len(queued),
        "queued": queued
    }

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "ابحث عن أخبار الذكاء الاصطناعي"
    print(json.dumps(execute_goal(goal), ensure_ascii=False, indent=2))
