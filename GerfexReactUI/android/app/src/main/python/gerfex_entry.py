import json
import os
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent / "GerfexIntegratedV1"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

APP_HOME = Path(os.environ.get("HOME", str(Path.cwd()))) / "gerfex_runtime_data"
APP_HOME.mkdir(parents=True, exist_ok=True)
os.environ["GERFEX_APP_HOME"] = str(APP_HOME)

for name in ["learning", "memory", "runtime", "logs", "queue"]:
    (APP_HOME / name).mkdir(parents=True, exist_ok=True)

os.chdir(str(APP_HOME))

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
                "storage": str(APP_HOME),
                "raw": result
            }, ensure_ascii=False)

        return json.dumps({"ok": True, "reply": str(result), "storage": str(APP_HOME)}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "ok": False,
            "reply": "خطأ داخلي في Gerfex Standalone: " + str(e),
            "storage": str(APP_HOME)
        }, ensure_ascii=False)
