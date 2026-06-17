import json
from cognitive.action_selector import select_action

def create_plan(goal, understanding):
    selected = select_action(goal, {
        "understanding": understanding
    })

    return {
        "ok": selected.get("ok", False),
        "action": selected.get("action"),
        "reason": selected.get("reason"),
        "confidence": selected.get("confidence"),
        "steps": selected.get("steps", []),
        "source": "ActionSelectorV1"
    }

if __name__ == "__main__":
    demo_understanding = {
        "screen_type": "browser",
        "summary": "Google Chrome browser",
        "capabilities": ["navigate", "search", "open_url", "read_page"],
        "confidence": 0.95
    }

    print(json.dumps(
        create_plan("حلل الشاشة الحالية", demo_understanding),
        ensure_ascii=False,
        indent=2
    ))
