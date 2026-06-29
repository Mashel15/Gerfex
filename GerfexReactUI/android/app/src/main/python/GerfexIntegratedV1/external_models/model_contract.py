EXTERNAL_MODEL_CONTRACT_V1 = {
    "role": "advisor_only",
    "can_execute": False,
    "can_modify_files": False,
    "can_control_android": False,
    "can_override_gerfex_core": False,
    "output_type": "advice",
    "authority": "Gerfex Core remains final decision owner"
}

def enforce_contract(result):
    if not isinstance(result, dict):
        result = {"reply": str(result)}

    return {
        "ok": bool(result.get("ok", True)),
        "role": "external_model_advisor",
        "reply": result.get("reply") or result.get("advice") or "",
        "provider": result.get("provider", "unknown"),
        "model": result.get("model", "unknown"),
        "raw": result,
        "contract": EXTERNAL_MODEL_CONTRACT_V1
    }
