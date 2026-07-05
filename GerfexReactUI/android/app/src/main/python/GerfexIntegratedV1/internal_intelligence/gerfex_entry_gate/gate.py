ALLOWED_ROUTES = {
    "learning_to_gerfex",
    "main_gma_to_gerfex",
    "gerfex_to_internal_model",
    "gerfex_to_external_model",
}


def _base_response(ok, route, payload=None, error=None, reply=""):
    payload = payload or {}
    return {
        "ok": ok,
        "route": route,
        "direction": payload.get("direction"),
        "surface": payload.get("surface"),
        "mode": payload.get("mode"),
        "message": payload.get("message"),
        "target_model": payload.get("target_model"),
        "context": payload.get("context", {}),
        "error": error,
        "reply": reply,
    }


def gateway(route, payload=None):
    payload = payload or {}

    if route not in ALLOWED_ROUTES:
        return _base_response(
            False,
            route,
            payload,
            error="invalid_gerfex_intelligence_gateway_route",
            reply="مسار التواصل بين Gerfex ونموذج الذكاء غير معتمد."
        )

    return _base_response(True, route, payload)


def enter_gerfex(route, payload=None):
    payload = payload or {}
    payload["direction"] = "model_to_gerfex"
    return gateway(route, payload)


def exit_gerfex(route, payload=None):
    payload = payload or {}
    payload["direction"] = "gerfex_to_model"
    return gateway(route, payload)


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
        "target_model": "GMA",
    })


def gerfex_to_internal_model(message, target_model="GMA", context=None):
    return exit_gerfex("gerfex_to_internal_model", {
        "surface": "gerfex_core",
        "mode": "internal_model_request",
        "message": message,
        "target_model": target_model,
        "context": context or {},
    })


def gerfex_to_external_model(message, target_model, context=None):
    return exit_gerfex("gerfex_to_external_model", {
        "surface": "gerfex_core",
        "mode": "external_model_request",
        "message": message,
        "target_model": target_model,
        "context": context or {},
    })
