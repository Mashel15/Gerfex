from core.gerfex_core import run_goal


def classify_main_surface(message, model_state=None):
    text = (message or "").strip().lower()

    # Structural Cleanup Gate V1:
    # Gerfex Core receives only direct commands that are currently confirmed
    # as Gerfex-owned capabilities. Everything else goes to GMA native.
    direct_core_markers = [
        "كروم", "chrome",
        "يوتيوب", "youtube",
        "الإعدادات", "الاعدادات", "اعدادات", "settings",
        "الرئيسية", "home",
        "ارجع", "back",
    ]

    if any(w in text for w in direct_core_markers):
        return {
            "path": "gerfex_core",
            "reason": "main_surface_confirmed_gerfex_core_capability"
        }

    return {
        "path": "gerfex_brain",
        "reason": "main_surface_to_gma_native_by_default"
    }


def think_main_surface(message, model_state=None, trace=None):
    route = classify_main_surface(message, model_state)

    if route.get("path") == "gerfex_brain":
        return {
            "ok": True,
            "surface": "main",
            "speaker": "Gerfex",
            "path": "gerfex_brain",
            "route_reason": route.get("reason"),
            "needs_gma_native": True,
            "gma_mode": "main",
            "gma_prompt": message,
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
