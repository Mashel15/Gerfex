# Legacy external model gateway disabled by Gerfex Intelligence Gateway policy.
#
# Official external/internal model boundary:
# internal_intelligence/gerfex_entry_gate/
#
# No Gerfex component should call external models directly from here.


def ask_external_models(prompt, context=None):
    return {
        "ok": False,
        "reason": "legacy_external_models_gateway_disabled_by_policy",
        "reply": "",
        "required_route": "internal_intelligence.gerfex_entry_gate.gerfex_to_external_model",
    }


def ask_model(*args, **kwargs):
    return {
        "ok": False,
        "reason": "legacy_external_model_direct_call_disabled_by_policy",
        "reply": "",
        "required_route": "internal_intelligence.gerfex_entry_gate.gerfex_to_external_model",
    }


def ask_enabled_models(*args, **kwargs):
    return {
        "ok": False,
        "reason": "legacy_external_models_gateway_disabled_by_policy",
        "reply": "",
        "required_route": "internal_intelligence.gerfex_entry_gate.gerfex_to_external_model",
    }
