def select_action(goal, perception):
    goal = (goal or "").strip()
    understanding = perception.get("understanding", perception) if isinstance(perception, dict) else {}
    screen_type = understanding.get("screen_type", "unknown")
    caps = understanding.get("capabilities", []) or []

    if screen_type == "browser":
        if "حلل" in goal or "الشاشة" in goal:
            return {
                "ok": True,
                "action": "read_page" if "read_page" in caps else "inspect_browser",
                "reason": "browser_screen_analysis",
                "confidence": 0.9,
                "steps": ["read_visible_page", "summarize_screen"]
            }

        if "ابحث" in goal or "بحث" in goal:
            return {
                "ok": True,
                "action": "search_web",
                "reason": "browser_search_goal",
                "confidence": 0.9,
                "steps": ["focus_search_box", "type_query", "press_enter"]
            }

    if "افتح" in goal:
        return {
            "ok": True,
            "action": "open_app",
            "reason": "open_request_detected",
            "confidence": 0.85,
            "steps": ["resolve_target", "queue_open_app"]
        }

    return {
        "ok": True,
        "action": "unknown",
        "reason": "no_rule_matched",
        "confidence": 0.2,
        "steps": []
    }
