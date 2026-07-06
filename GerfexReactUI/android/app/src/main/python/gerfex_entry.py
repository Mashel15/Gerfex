import json
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent / "GerfexIntegratedV1"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from GerfexIntegratedV1.gerfex_android_paths import ensure_dirs
from runtime.execution_trace import new_trace, add_stage, save_trace

APP_HOME = ensure_dirs()

def think(message, model_state_json=None):
    """
    Legacy compatibility entry.

    This old entry must not call run_goal, brain_manager, external_models,
    or any model provider directly.

    Official main route is:
    think -> think_main -> main_surface -> main_core_gate
    -> gma/main if needed -> gerfex_entry_gate.
    """
    return think_main(message, model_state_json)
def think_main(message, model_state_json=None):
    """Main screen entry. User is talking to Gerfex."""
    trace = new_trace(message)
    add_stage(trace, "main_surface_received", source="gerfex_entry", goal=message)

    try:
        try:
            model_state = json.loads(model_state_json or "{}") if isinstance(model_state_json, str) else (model_state_json or {})
        except Exception:
            model_state = {}

        from GerfexIntegratedV1.surfaces.main_surface import think_main_surface

        result = think_main_surface(message, model_state=model_state, trace=trace)
        add_stage(trace, "main_surface_done", source="gerfex_entry", ok=result.get("ok"), path=result.get("path"))
        save_trace(trace)

        return json.dumps({
            "ok": result.get("ok", True),
            "speaker": "Gerfex",
            "reply": result.get("reply", "تم تنفيذ الطلب داخل Gerfex."),
            "surface": "main",
            "path": result.get("path"),
            "route_reason": result.get("route_reason"),
            "needs_gma_native": result.get("needs_gma_native", False),
            "gma_mode": result.get("gma_mode"),
            "gma_prompt": result.get("gma_prompt"),
            "storage": str(APP_HOME),
            "trace_id": trace.get("trace_id"),
            "raw": result.get("raw")
        }, ensure_ascii=False)

    except Exception as e:
        add_stage(trace, "main_surface_exception", source="gerfex_entry", error=str(e))
        try:
            save_trace(trace)
        except Exception:
            pass

        return json.dumps({
            "ok": False,
            "speaker": "Gerfex",
            "reply": "خطأ داخلي في مسار Gerfex الرئيسي: " + str(e),
            "surface": "main",
            "trace_id": trace.get("trace_id")
        }, ensure_ascii=False)


def think_learning(message, learning_state_json=None):
    """Learning page entry. User is talking directly to GMA."""
    trace = new_trace(message)
    add_stage(trace, "learning_surface_received", source="gerfex_entry", goal=message)

    try:
        try:
            learning_state = json.loads(learning_state_json or "{}") if isinstance(learning_state_json, str) else (learning_state_json or {})
        except Exception:
            learning_state = {}

        from GerfexIntegratedV1.surfaces.learning_surface import think_learning_surface

        result = think_learning_surface(message, learning_state=learning_state)
        add_stage(trace, "learning_surface_done", source="gerfex_entry", ok=result.get("ok"), mode=result.get("gma_mode"))
        save_trace(trace)

        return json.dumps({
            "ok": result.get("ok", False),
            "speaker": "GMA",
            "reply": result.get("reply", "لم أستطع توليد رد تعلم الآن."),
            "surface": "learning",
            "needs_gma_native": result.get("needs_gma_native", False),
            "gma_mode": result.get("gma_mode"),
            "gma_prompt": result.get("gma_prompt"),
            "trace_id": trace.get("trace_id"),
            "raw": result.get("raw")
        }, ensure_ascii=False)

    except Exception as e:
        add_stage(trace, "learning_surface_exception", source="gerfex_entry", error=str(e))
        try:
            save_trace(trace)
        except Exception:
            pass

        return json.dumps({
            "ok": False,
            "speaker": "GMA",
            "reply": "خطأ داخلي في مسار تعلم GMA: " + str(e),
            "surface": "learning",
            "trace_id": trace.get("trace_id")
        }, ensure_ascii=False)

def learning_status():
    try:
        from GerfexIntegratedV1.internal_intelligence.learning.learning_manager import (
            pending_lessons,
            pending_improvements,
            approved_knowledge,
            approved_improvements,
        )

        return json.dumps({
            "ok": True,
            "pending_lessons": pending_lessons(),
            "pending_improvements": pending_improvements(),
            "approved_knowledge": approved_knowledge(),
            "approved_improvements": approved_improvements(),
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": str(e)
        }, ensure_ascii=False)


def approve_latest_lesson_entry():
    try:
        from GerfexIntegratedV1.internal_intelligence.learning.learning_manager import approve_latest_lesson
        return json.dumps(approve_latest_lesson(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def approve_latest_improvement_entry():
    try:
        from GerfexIntegratedV1.internal_intelligence.learning.learning_manager import approve_latest_improvement
        return json.dumps(approve_latest_improvement(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
