import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "GerfexIntegratedV1"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gerfex_core import run_goal

def think(message):
    try:
        result = run_goal(message)
        if isinstance(result, dict):
            execution = result.get("execution", {})
            decision = result.get("decision", {})
            reply = (
                execution.get("reply")
                or execution.get("message")
                or execution.get("reason")
                or decision.get("reason")
                or "تم تنفيذ الطلب داخل Gerfex."
            )
            return json.dumps({
                "ok": result.get("ok", True),
                "reply": reply,
                "raw": result
            }, ensure_ascii=False)
        return json.dumps({"ok": True, "reply": str(result)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "ok": False,
            "reply": "خطأ داخلي في Gerfex Standalone: " + str(e)
        }, ensure_ascii=False)
