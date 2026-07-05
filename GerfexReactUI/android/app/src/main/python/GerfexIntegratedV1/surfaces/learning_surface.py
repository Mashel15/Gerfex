def think_learning_surface(message, learning_state=None):
    return {
        "ok": True,
        "surface": "learning",
        "speaker": "GMA",
        "needs_gma_native": True,
        "gma_mode": "learning",
        "gma_prompt": message,
        "reply": ""
    }
