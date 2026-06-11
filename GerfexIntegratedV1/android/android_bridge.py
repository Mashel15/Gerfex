import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_FILE = ROOT / "runtime" / "android_queue.txt"

def queue_action(action):
    if not action:
        return {
            "ok": False,
            "reason": "no_action"
        }

    item = {
        "time": time.time(),
        "action": action.get("action"),
        "args": action.get("args", {}),
        "source": "GerfexIntegratedV1"
    }

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "queued": item,
        "queue_file": str(QUEUE_FILE)
    }
