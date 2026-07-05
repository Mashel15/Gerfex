from core.gerfex_core import run_goal
from GerfexIntegratedV1.surfaces.main_core_gate import classify_main_command
from GerfexIntegratedV1.internal_intelligence.gerfex_entry_gate.gate import enter_from_main_gma


def classify_main_surface(message, model_state=None):
    return classify_main_command(message, model_state=model_state)


def think_main_surface(message, model_state=None, trace=None):
    route = classify_main_surface(message, model_state)

    if route.get("path") == "gerfex_brain":
        gate_result = enter_from_main_gma(message, context={
            "route_reason": route.get("reason"),
            "model_state": model_state or {}
        })

        return {
            "ok": True,
            "surface": "main",
            "speaker": "Gerfex",
            "path": "gerfex_brain",
            "route_reason": route.get("reason"),
            "needs_gma_native": True,
            "gma_mode": "main",
            "gma_prompt": message,
            "gerfex_entry_gate": gate_result,
            "reply": ""
        }

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
