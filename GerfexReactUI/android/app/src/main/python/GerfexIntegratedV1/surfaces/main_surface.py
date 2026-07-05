from core.gerfex_core import run_goal
from GerfexIntegratedV1.surfaces.main_core_gate import classify_main_command
from GerfexIntegratedV1.internal_intelligence.gma.main.gma_main_entry import think_gma_main_entry


def classify_main_surface(message, model_state=None):
    return classify_main_command(message, model_state=model_state)


def think_main_surface(message, model_state=None, trace=None):
    route = classify_main_surface(message, model_state)

    if route.get("path") == "gerfex_brain":
        result = think_gma_main_entry(
            message,
            model_state=model_state,
            route_context={"route_reason": route.get("reason")}
        )
        result["route_reason"] = route.get("reason")
        return result

    result = run_goal(message, trace=trace)

    execution = result.get("execution", {}) if isinstance(result, dict) else {}
    decision = result.get("decision", {}) if isinstance(result, dict) else {}

    reply = (
        execution.get("reply")
        or execution.get("message")
        or execution.get("reason")
        or decision.get("reason")
        or "تم تنفيذ الطلب داخل Gerfex."
    )

    return {
        "ok": bool(result.get("ok", True)) if isinstance(result, dict) else True,
        "surface": "main",
        "speaker": "Gerfex",
        "path": route.get("path"),
        "route_reason": route.get("reason"),
        "needs_gma_native": False,
        "reply": reply,
        "raw": result
    }
