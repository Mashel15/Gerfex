def advise(goal, memory_recall):
    matches = memory_recall.get("matches", []) if isinstance(memory_recall, dict) else []

    success = [m for m in matches if m.get("ok") is True]
    failure = [m for m in matches if m.get("ok") is False]

    targets = {}
    routes = {}

    for m in success:
        t = m.get("target")
        if t:
            targets[t] = targets.get(t, 0) + 1

        r = m.get("route")
        if isinstance(r, dict):
            route = r.get("route")
            if route:
                routes[route] = routes.get(route, 0) + 1

    best_target = max(targets, key=targets.get) if targets else None
    best_route = max(routes, key=routes.get) if routes else None

    total = len(matches)
    confidence = round(len(success) / total, 2) if total else 0

    return {
        "ok": True,
        "goal": goal,
        "success_count": len(success),
        "failure_count": len(failure),
        "recommended_route": best_route,
        "recommended_target": best_target,
        "confidence": confidence,
        "note": "Memory Advisor لخص الخبرة السابقة بدون ضغط على Queen"
    }
