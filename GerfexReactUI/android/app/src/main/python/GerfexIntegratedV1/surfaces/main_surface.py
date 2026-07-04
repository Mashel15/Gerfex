from core.gerfex_core import run_goal


def classify_main_surface(message, model_state=None):
    text = (message or "").strip().lower()

    gerfex_core_words = [
        "افتح", "ارجع", "الرئيسية", "home", "back",
        "كروم", "يوتيوب", "الإعدادات", "الاعدادات",
        "ابحث", "بحث", "نفذ", "نفّذ"
    ]

    if any(w in text for w in gerfex_core_words):
        return {"path": "gerfex_core", "reason": "main_surface_core_capability"}

    return {"path": "gerfex_brain", "reason": "main_surface_internal_brain_needed"}


def think_main_surface(message, model_state=None, trace=None):
    route = classify_main_surface(message, model_state)

    # Safe first version:
    # Both branches return through Gerfex identity.
    # The deeper separation between Gerfex-only and GMA-assisted reasoning
    # will be refined after this surface layer is connected.
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
        "reply": reply,
        "raw": result
    }
