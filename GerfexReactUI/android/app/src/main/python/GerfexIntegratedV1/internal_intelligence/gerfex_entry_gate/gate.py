ALLOWED_ROUTES = {
    "learning_to_gerfex",
    "main_gma_to_gerfex",
}


def enter_gerfex(route, payload=None):
    payload = payload or {}

    if route not in ALLOWED_ROUTES:
        return {
            "ok": False,
            "route": route,
            "error": "invalid_internal_intelligence_gerfex_route",
            "reply": "مسار دخول الذكاء الداخلي إلى Gerfex غير معتمد."
        }

    return {
        "ok": True,
        "route": route,
        "surface": payload.get("surface"),
        "mode": payload.get("mode"),
        "message": payload.get("message"),
        "context": payload.get("context", {}),
        "reply": ""
    }


def enter_from_learning(message, context=None):
    return enter_gerfex("learning_to_gerfex", {
        "surface": "learning",
        "mode": "learning",
        "message": message,
        "context": context or {},
    })


def enter_from_main_gma(message, context=None):
    return enter_gerfex("main_gma_to_gerfex", {
        "surface": "main",
        "mode": "main_gma",
        "message": message,
        "context": context or {},
    })
