def think(prompt, context=None, mode="general"):
    text = (prompt or "").strip()
    return {
        "reply": "Dummy Brain: استلمت الرسالة، لكن لا يوجد نموذج ذكاء فعلي متصل حالياً.",
        "intent": "chat",
        "suggested_action": None,
        "confidence": 0.30,
        "provider": "dummy",
        "status": "fallback",
        "mode": mode
    }
