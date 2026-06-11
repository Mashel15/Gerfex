from android.android_bridge import queue_action
from safety.safety_guard import check_action

def _block(action, safety):
    return {
        "ok": False,
        "blocked": True,
        "action": action,
        "safety": safety
    }

def execute(decision):
    if not decision.get("ok"):
        return {"ok": False, "reason": "decision_not_ok", "decision": decision}

    actions = decision.get("actions")
    if actions:
        results = []
        all_ok = True

        for action in actions:
            safety = check_action(action)
            if not safety.get("allowed"):
                results.append(_block(action, safety))
                all_ok = False
                continue

            r = queue_action(action)
            r["safety"] = safety
            results.append(r)

            if not r.get("ok"):
                all_ok = False

        return {
            "ok": all_ok,
            "queued_count": sum(1 for r in results if r.get("ok")),
            "blocked_count": sum(1 for r in results if r.get("blocked")),
            "results": results,
            "decision": decision
        }

    action = decision.get("action")
    if action:
        safety = check_action(action)
        if not safety.get("allowed"):
            return {
                "ok": False,
                "blocked": True,
                "action": action,
                "safety": safety,
                "decision": decision
            }

        result = queue_action(action)
        result["safety"] = safety

        return {
            "ok": bool(result.get("ok")),
            "queued": result,
            "decision": decision
        }

    return {"ok": False, "reason": "no_executable_action", "decision": decision}
