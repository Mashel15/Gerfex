import json
import time
from gerfex_android_paths import app_path

QUEUE_FILE = app_path("runtime", "android_queue.txt")

def queue_action(action):
    if not action:
        return {"ok": False, "reason": "no_action"}

    item = {
        "time": time.time(),
        "action": action.get("action"),
        "args": action.get("args", {}),
        "source": "GerfexIntegratedV1"
    }

    # Android standalone mode: return action for native Java executor.
    # Also keep queue log for memory/debug, but execution is no longer external.
    try:
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with QUEUE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return {
        "ok": True,
        "native_action": item,
        "queued": item,
        "queue_file": str(QUEUE_FILE)
    }
