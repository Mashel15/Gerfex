from core.gerfex_core import run_goal
from GerfexIntegratedV1.surfaces.main_core_gate import classify_main_command
from GerfexIntegratedV1.internal_intelligence.gma.main.gma_main_entry import think_gma_main_entry


def classify_main_surface(message, model_state=None):
    return classify_main_command(message, model_state=model_state)


def _looks_like_execution_route(route: dict) -> bool:
    if not isinstance(route, dict):
        return False

    path = (route.get("path") or "").strip()
    reason = (route.get("reason") or "").strip().lower()

    if path in {
        "android_execution",
        "android_action",
        "gerfex_execution",
        "tool_execution",
        "open_app",
        "search_web",
        "device_action",
        "gerfex_core",
    }:
        return True

    execution_markers = [
        "open_app",
        "android",
        "execute",
        "action",
        "tool",
        "device",
        "command",
        "تنفيذ",
        "افتح",
        "شغّل",
        "ابحث",
        "افتح التطبيق",
        "نفذ",
    ]
    return any(marker in reason for marker in execution_markers)


def think_main_surface(message, model_state=None, trace=None):
    route = classify_main_surface(message, model_state)

    if not _looks_like_execution_route(route):
        result = think_gma_main_entry(
            message,
            model_state=model_state,
            route_context={
                "route_reason": route.get("reason"),
                "source_surface": "main",
                "route_path": route.get("path"),
            },
        )

        if not isinstance(result, dict):
            result = {
                "ok": False,
                "reply": "تعذر الحصول على رد من GMA.",
                "surface": "main",
                "speaker": "Gerfex",
                "path": "gerfex_brain",
                "needs_gma_native": False,
                "raw": result,
            }

        result.setdefault("surface", "main")
        result.setdefault("speaker", "Gerfex")
        result.setdefault("path", "gerfex_brain")
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
        "path": route.get("path") or "execution",
        "route_reason": route.get("reason"),
        "needs_gma_native": False,
        "reply": reply,
        "raw": result,
    }
