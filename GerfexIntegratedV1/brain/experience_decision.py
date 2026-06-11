def apply_experience_advice(goal, decision, memory_advice):
    if not isinstance(decision, dict):
        decision = {}

    if not isinstance(memory_advice, dict) or not memory_advice.get("ok"):
        decision["experience_used"] = False
        return decision

    confidence = memory_advice.get("confidence", 0)
    target = memory_advice.get("recommended_target")
    route = memory_advice.get("recommended_route")

    decision["experience_advice"] = {
        "route": route,
        "target": target,
        "confidence": confidence,
        "note": "Experience Decision استخدم خبرة Gerfex السابقة قبل التنفيذ"
    }

    decision["experience_used"] = confidence >= 0.5

    if decision["experience_used"]:
        if target and not decision.get("target"):
            decision["target"] = target
        if route:
            decision["experience_route"] = route

    return decision
