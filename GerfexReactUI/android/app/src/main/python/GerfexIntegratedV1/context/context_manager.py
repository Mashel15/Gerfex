import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from android.android_bridge import queue_action

def prepare_context(goal):

    goal = (goal or "").strip()

    if "ابحث" in goal or "بحث" in goal:

        queue_action({
            "action": "open_app",
            "args": {
                "package": "chrome"
            }
        })

        queue_action({
            "action": "wait",
            "args": {
                "seconds": 3
            }
        })

        queue_action({
            "action": "dump_ui",
            "args": {}
        })

        return {
            "ok": True,
            "context": "chrome",
            "reason": "search_goal_detected"
        }

    return {
        "ok": True,
        "context": "current_screen",
        "reason": "no_context_change_needed"
    }

if __name__ == "__main__":
    print(
        json.dumps(
            prepare_context(
                "ابحث عن أخبار الذكاء الاصطناعي"
            ),
            ensure_ascii=False,
            indent=2
        )
    )
