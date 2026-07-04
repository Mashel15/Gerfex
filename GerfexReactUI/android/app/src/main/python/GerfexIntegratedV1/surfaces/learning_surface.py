from internal_intelligence.provider.provider_loader import load_provider


def think_learning_surface(message, learning_state=None):
    provider = load_provider("gma")

    if provider is None:
        return {
            "ok": False,
            "surface": "learning",
            "speaker": "GMA",
            "reply": "GMA provider غير متاح الآن.",
            "reason": "gma_provider_not_available"
        }

    result = provider.think(
        message,
        context={
            "mode": "learning",
            "surface": "gma_learning"
        }
    )

    thought = result.get("thought", {}) if isinstance(result, dict) else {}
    reply = (
        thought.get("answer")
        or thought.get("reply")
        or thought.get("message")
        or result.get("reply")
        or "لم أستطع توليد رد تعلم الآن."
    )

    return {
        "ok": bool(result.get("ok", False)) if isinstance(result, dict) else False,
        "surface": "learning",
        "speaker": "GMA",
        "reply": reply,
        "raw": result
    }
