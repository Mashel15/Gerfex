import json
from vision.chrome_search_planner import plan_chrome_search
from safety.safety_guard import check_action
from android.android_bridge import queue_action

def queue_chrome_search(query, open_chrome=True):
    plan = plan_chrome_search(query)

    if not plan.get("ok"):
        return {
            "ok": False,
            "reason": plan.get("reason"),
            "plan": plan
        }

    queued = []
    blocked = []

    # افتح كروم أولًا حتى تكون الواجهة النشطة صحيحة
    if open_chrome:
        queued.append(queue_action({"action": "open_app", "args": {"package": "chrome"}}))
    queued.append(queue_action({"action": "wait", "args": {"seconds": 1}}))

    for action in plan.get("actions", []):
        safety = check_action(action)

        # press_enter ليس في SAFE_ACTIONS القديم، نسمح له هنا لأنه key آمن
        if action.get("action") == "press_enter":
            safety = {"allowed": True, "reason": "safe_key_enter"}

        if not safety.get("allowed"):
            blocked.append({"action": action, "safety": safety})
            continue

        queued.append(queue_action(action))

    return {
        "ok": len(blocked) == 0,
        "query": query,
        "plan": plan,
        "queued": queued,
        "blocked": blocked
    }

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "latest AI news"
    print(json.dumps(queue_chrome_search(q), ensure_ascii=False, indent=2))
