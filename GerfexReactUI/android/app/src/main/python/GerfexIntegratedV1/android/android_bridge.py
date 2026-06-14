import time

def queue_action(action):
    if not action:
        return {"ok": False, "reason": "no_action"}

    item = {
        "time": time.time(),
        "action": action.get("action"),
        "args": action.get("args", {}),
        "source": "GerfexIntegratedV1"
    }

    # APK standalone mode:
    # Return native_action for GerfexPlugin Java executor.
    # No external legacy queue dependency.
    return {
        "ok": True,
        "native_action": item
    }
