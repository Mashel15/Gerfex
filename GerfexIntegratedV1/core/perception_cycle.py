import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation.screen_observer import observe
from understanding.screen_understanding import understand_screen
from planner.action_planner import create_plan

def run_perception_cycle(goal):
    observation = observe()
    understanding = understand_screen(observation)
    plan = create_plan(goal, understanding)

    return {
        "ok": bool(observation.get("ok") and understanding.get("ok") and plan.get("ok")),
        "goal": goal,
        "observation": {
            "top_package": observation.get("top_package"),
            "item_count": observation.get("item_count"),
            "clickable_count": observation.get("clickable_count")
        },
        "understanding": {
            "screen_type": understanding.get("screen_type"),
            "summary": understanding.get("summary"),
            "capabilities": understanding.get("capabilities"),
            "confidence": understanding.get("confidence")
        },
        "plan": plan
    }

if __name__ == "__main__":
    import sys
    goal = " ".join(sys.argv[1:]) or "ابحث عن أخبار الذكاء الاصطناعي"
    print(json.dumps(run_perception_cycle(goal), ensure_ascii=False, indent=2))
