from android.android_bridge import queue_action
from safety.safety_guard import check_action
from vision.semantic_target_finder import find_semantic_target

def queue_semantic_tap(role, app="chrome", wait_before=2, wait_after=2):
    found = find_semantic_target(role)
    best = found.get("best")

    if not best:
        return {"ok": False, "reason": "target_not_found", "found": found}

    if not best.get("clickable"):
        return {"ok": False, "reason": "target_not_clickable", "target": best, "found": found}

    center = best.get("center")
    if not center:
        return {"ok": False, "reason": "target_has_no_center", "target": best, "found": found}

    tap_action = {"action": "tap", "args": {"x": center[0], "y": center[1]}}
    safety = check_action(tap_action)

    if not safety.get("allowed"):
        return {"ok": False, "reason": "safety_blocked", "safety": safety, "target": best}

    queued = []
    queued.append(queue_action({"action": "open_app", "args": {"package": app}}))
    queued.append(queue_action({"action": "wait", "args": {"seconds": wait_before}}))
    queued.append(queue_action(tap_action))
    queued.append(queue_action({"action": "wait", "args": {"seconds": wait_after}}))
    queued.append(queue_action({"action": "dump_ui", "args": {"focus": app}}))

    return {
        "ok": True,
        "role": role,
        "app": app,
        "target": best,
        "tap_action": tap_action,
        "safety": safety,
        "queued": queued
    }

if __name__ == "__main__":
    import sys, json
    role = sys.argv[1] if len(sys.argv) > 1 else "search"
    app = sys.argv[2] if len(sys.argv) > 2 else "chrome"
    print(json.dumps(queue_semantic_tap(role, app), ensure_ascii=False, indent=2))
