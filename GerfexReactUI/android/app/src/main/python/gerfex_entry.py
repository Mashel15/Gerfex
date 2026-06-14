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
from runtime.execution_trace import new_trace, add_stage, save_trace

def think(message):
    trace = new_trace(message)
    add_stage(trace, "goal_received", source="gerfex_entry", goal=message)

    try:
        add_stage(trace, "run_goal_start", source="gerfex_entry")
        result = run_goal(message, trace=trace)
        add_stage(trace, "run_goal_end", source="gerfex_core", result_type=type(result).__name__)

        if isinstance(result, dict):
            execution = result.get("execution", {})
            decision = result.get("decision", {})

            add_stage(
                trace,
                "decision_observed",
                source="gerfex_entry",
                intent=decision.get("intent"),
                target=decision.get("target"),
                decision_ok=decision.get("ok")
            )

            native_actions = execution.get("native_actions", [])
            add_stage(
                trace,
                "execution_observed",
                source="gerfex_entry",
                execution_ok=execution.get("ok"),
                native_action_count=len(native_actions) if isinstance(native_actions, list) else 0
            )

            reply = (
                execution.get("reply")
                or execution.get("message")
                or execution.get("reason")
                or decision.get("reason")
                or "تم تنفيذ الطلب داخل Gerfex."
            )

            trace_path = save_trace(trace)

            return json.dumps({
                "ok": result.get("ok", True),
                "reply": reply,
                "storage": str(APP_HOME),
                "trace_id": trace.get("trace_id"),
                "trace_path": trace_path,
                "raw": result
            }, ensure_ascii=False)

        add_stage(trace, "non_dict_result", source="gerfex_entry", value=str(result)[:300])
        trace_path = save_trace(trace)

        return json.dumps({
            "ok": True,
            "reply": str(result),
            "storage": str(APP_HOME),
            "trace_id": trace.get("trace_id"),
            "trace_path": trace_path
        }, ensure_ascii=False)

    except Exception as e:
        add_stage(trace, "exception", source="gerfex_entry", error=str(e))
        trace_path = save_trace(trace)

        return json.dumps({
            "ok": False,
            "reply": "خطأ داخلي في Gerfex Standalone: " + str(e),
            "storage": str(APP_HOME),
            "trace_id": trace.get("trace_id"),
            "trace_path": trace_path
        }, ensure_ascii=False)
