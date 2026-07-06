import json
from pathlib import Path

from GerfexIntegratedV1.gerfex_android_paths import app_path
from .model_contract import enforce_contract

REGISTRY = app_path("external_models", "registry.json")

def _load_registry():
    if not REGISTRY.exists():
        return {"version": "EXTERNAL_MODELS_REGISTRY_V1", "mode": "advisor_only", "active": [], "providers": []}
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {"version": "EXTERNAL_MODELS_REGISTRY_V1", "mode": "advisor_only", "active": [], "providers": []}

def list_models():
    reg = _load_registry()
    return {
        "ok": True,
        "mode": "advisor_only",
        "active": reg.get("active", []),
        "providers": reg.get("providers", [])
    }

def ask_external_models(prompt, context=None):
    reg = _load_registry()
    active = reg.get("active", [])
    providers = reg.get("providers", [])

    if not active:
        return {
            "ok": True,
            "mode": "advisor_only",
            "reply": "لا يوجد نموذج خارجي مفعّل حالياً. البوابة جاهزة فقط.",
            "advisors": []
        }

    advisors = []
    for name in active:
        provider = next((p for p in providers if p.get("name") == name), {"name": name})
        kind = provider.get("type", "openai_compatible")

        if kind == "openai_compatible":
            from .providers.openai_compatible import ask
            res = ask(prompt, provider)
        else:
            res = {
                "ok": False,
                "provider": name,
                "reply": "نوع النموذج غير مدعوم حالياً: " + kind
            }

        advisors.append(enforce_contract(res))

    return {
        "ok": True,
        "mode": "advisor_only",
        "reply": "تمت استشارة النماذج الخارجية المسجلة.",
        "advisors": advisors,
        "providers": providers
    }


def test_model_connection(name):
    reg = _load_registry()
    providers = reg.get("providers", [])
    provider = next((p for p in providers if p.get("name") == name), None)

    if not provider:
        return {
            "ok": False,
            "provider": name,
            "reply": "النموذج غير موجود في registry."
        }

    if provider.get("hold"):
        return {
            "ok": False,
            "provider": name,
            "reply": "النموذج في وضع HOLD ولا يسمح له بالاختبار."
        }

    kind = provider.get("type", "openai_compatible")

    if kind == "openai_compatible":
        from .providers.openai_compatible import ask
        res = ask("اختبار اتصال قصير. رد بكلمة: متصل", provider)
    else:
        res = {
            "ok": False,
            "provider": name,
            "reply": "نوع النموذج غير مدعوم حالياً: " + str(kind)
        }

    return enforce_contract(res)


def test_model_connection_json(name):
    import json
    try:
        return json.dumps(test_model_connection(name), ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "ok": False,
            "provider": name,
            "reply": "test_model_connection_json error: " + str(e)
        }, ensure_ascii=False)


def test_model_connection_from_registry_json(name, registry_json):
    import json
    try:
        reg = json.loads(registry_json or "{}")
        providers = reg.get("providers", [])
        provider = next((p for p in providers if p.get("name") == name), None)

        if not provider:
            return json.dumps({
                "ok": False,
                "provider": name,
                "reply": "النموذج غير موجود في registry المرسل من Java.",
                "providers_count": len(providers),
                "provider_names": [p.get("name") for p in providers]
            }, ensure_ascii=False)

        if provider.get("hold"):
            return json.dumps({
                "ok": False,
                "provider": name,
                "reply": "النموذج في وضع HOLD ولا يسمح له بالاختبار."
            }, ensure_ascii=False)

        kind = provider.get("type", "openai_compatible")

        if kind == "openai_compatible":
            from .providers.openai_compatible import ask
            res = ask("اختبار اتصال قصير. رد بكلمة: متصل", provider)
        else:
            res = {
                "ok": False,
                "provider": name,
                "reply": "نوع النموذج غير مدعوم حالياً: " + str(kind)
            }

        return json.dumps(enforce_contract(res), ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "ok": False,
            "provider": name,
            "reply": "test_model_connection_from_registry_json error: " + str(e)
        }, ensure_ascii=False)
