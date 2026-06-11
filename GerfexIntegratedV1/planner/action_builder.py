import json
from urllib.parse import quote_plus

def _extract_query(goal):
    query = (goal or "").strip()

    for marker in ["ابحث عن", "بحث عن", "search for", "search"]:
        if marker in query:
            query = query.split(marker, 1)[1].strip()

    return query or goal

def build_actions(goal, plan, understanding=None):
    goal = (goal or "").strip()
    understanding = understanding or {}
    action = plan.get("action")

    if action == "search_web":
        query = _extract_query(goal)
        url = "https://www.google.com/search?q=" + quote_plus(query)

        return {
            "ok": True,
            "mode": "action_builder_v2",
            "strategy": "open_url",
            "intent": "search_web",
            "query": query,
            "action_bundle": [
                {
                    "action": "open_url",
                    "args": {
                        "url": url
                    },
                    "executable": True,
                    "reason": "stable_search_execution"
                }
            ]
        }

    if action == "open_app":
        return {
            "ok": True,
            "mode": "action_builder_v2",
            "intent": "open_app",
            "action_bundle": [
                {
                    "action": "open_app",
                    "args": {},
                    "executable": False,
                    "reason": "target_app_not_resolved_in_builder"
                }
            ]
        }

    return {
        "ok": False,
        "mode": "action_builder_v2",
        "intent": action or "unknown",
        "reason": "no_action_builder_rule",
        "action_bundle": []
    }

if __name__ == "__main__":
    demo_plan = {
        "ok": True,
        "action": "search_web",
        "steps": ["focus_search_box", "type_query", "press_enter"]
    }

    print(
        json.dumps(
            build_actions("ابحث عن أخبار الذكاء الاصطناعي", demo_plan),
            ensure_ascii=False,
            indent=2
        )
    )
