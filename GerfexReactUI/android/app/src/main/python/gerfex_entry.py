import json
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent / "GerfexIntegratedV1"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from GerfexIntegratedV1.gerfex_android_paths import ensure_dirs
from core.gerfex_core import run_goal
from GerfexIntegratedV1.external_models.model_gateway import ask_external_models
from runtime.execution_trace import new_trace, add_stage, save_trace

APP_HOME = ensure_dirs()

def think(message, model_state_json=None):
    trace = new_trace(message)
    add_stage(trace, "goal_received", source="gerfex_entry", goal=message)

    try:
        try:
            model_state = json.loads(model_state_json or "{}") if isinstance(model_state_json, str) else (model_state_json or {})
        except Exception:
            model_state = {}

        internal_brain_connected = bool(model_state.get("connected", True))

        external_advice = {"ok": True, "mode": "advisor_only", "advisors": [], "reply": "external_skipped_internal_brain_on"}

        if not internal_brain_connected:
            external_advice = ask_external_models(message, context={"mode": "advisor_only"})
            advisors = external_advice.get("advisors", []) if isinstance(external_advice, dict) else []
            first = advisors[0] if advisors else {}
            reply = (
                first.get("reply")
                or external_advice.get("reply")
                or "Gerfex متوقف لأن العقل الداخلي غير مفعل، ولا يوجد رد من الذكاء الخارجي."
            )

            add_stage(trace, "internal_brain_off_external_direct", source="gerfex_entry", advisors=len(advisors))
            save_trace(trace)

            return json.dumps({
                "ok": bool(first.get("ok", external_advice.get("ok", False))),
                "speaker": first.get("provider", "External AI"),
                "reply": reply,
                "mode": "internal_brain_off_external_direct",
                "external_models": external_advice,
                "storage": str(APP_HOME),
                "trace_id": trace.get("trace_id")
            }, ensure_ascii=False)
        add_stage(
            trace,
            "external_models_advice",
            source="external_models",
            ok=external_advice.get("ok"),
            mode=external_advice.get("mode"),
            advisors=len(external_advice.get("advisors", []))
        )

        add_stage(trace, "run_goal_start", source="gerfex_entry")
        result = run_goal(message, trace=trace)
        add_stage(trace, "run_goal_end", source="gerfex_core", result_type=type(result).__name__)

        if isinstance(result, dict):
            execution = result.get("execution", {}) or {}
            decision = result.get("decision", {}) or {}

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

            save_trace(trace)

            return json.dumps({
                "ok": result.get("ok", True),
                "reply": reply,
                "storage": str(APP_HOME),
                "trace_id": trace.get("trace_id"),
                "external_models": external_advice,
                "raw": result
            }, ensure_ascii=False)

        add_stage(trace, "non_dict_result", source="gerfex_entry", value=str(result)[:300])
        save_trace(trace)

        return json.dumps({
            "ok": True,
            "reply": str(result),
            "storage": str(APP_HOME),
            "trace_id": trace.get("trace_id")
        }, ensure_ascii=False)

    except Exception as e:
        add_stage(trace, "exception", source="gerfex_entry", error=str(e))
        try:
            save_trace(trace)
        except Exception:
            pass

        return json.dumps({
            "ok": False,
            "reply": "خطأ داخلي في Gerfex Standalone: " + str(e),
            "storage": str(APP_HOME),
            "trace_id": trace.get("trace_id")
        }, ensure_ascii=False)


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
    try:
        try:
            learning_state = json.loads(learning_state_json or "{}") if isinstance(learning_state_json, str) else (learning_state_json or {})
        except Exception:
            learning_state = {}

        from GerfexIntegratedV1.surfaces.learning_surface import think_learning_surface

        result = think_learning_surface(message, learning_state=learning_state)

        return json.dumps({
            "ok": result.get("ok", False),
            "speaker": "GMA",
            "reply": result.get("reply", "لم أستطع توليد رد تعلم الآن."),
            "surface": "learning",
            "needs_gma_native": result.get("needs_gma_native", False),
            "gma_mode": result.get("gma_mode"),
            "gma_prompt": result.get("gma_prompt"),
            "raw": result.get("raw")
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "ok": False,
            "speaker": "GMA",
            "reply": "خطأ داخلي في مسار تعلم GMA: " + str(e),
            "surface": "learning"
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
