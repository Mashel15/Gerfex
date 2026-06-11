def route(goal):
    text = (goal or "").strip().lower()

    news_words = ["أخبار", "خبر", "تابع", "news"]
    android_words = ["افتح", "كروم", "يوتيوب", "الإعدادات", "ارجع", "الرئيسية", "dump"]
    memory_words = ["تذكر", "احفظ", "ماذا تعرف", "ذاكرة"]
    cognitive_words = ["حلل", "خطط", "فكر", "راجع", "اقترح"]

    if any(w in text for w in news_words):
        return {"ok": True, "route": "research", "reason": "news/research goal"}

    if any(w in text for w in android_words):
        return {"ok": True, "route": "android", "reason": "android control goal"}

    if any(w in text for w in memory_words):
        return {"ok": True, "route": "memory", "reason": "memory goal"}

    if any(w in text for w in cognitive_words):
        return {"ok": True, "route": "cognitive", "reason": "thinking/planning goal"}

    return {"ok": True, "route": "queen", "reason": "default Queen reasoning"}
