def route(goal):
    text = (goal or "").strip().lower()

    news_words = ["أخبار", "اخبار", "خبر", "تابع", "news"]
    android_words = ["افتح", "كروم", "يوتيوب", "الإعدادات", "الاعدادات", "ارجع", "الرئيسية", "dump"]
    memory_words = ["تذكر", "احفظ", "ماذا تعرف", "ذاكرة"]
    cognitive_words = ["حلل", "خطط", "فكر", "راجع", "اقترح"]

    # Secondary systems / internal Gerfex tools
    if ("عامل الأهداف" in text) or ("عامل الاهداف" in text) or ("goal worker" in text):
        return {
            "ok": True,
            "route": "secondary",
            "system": "goal_worker",
            "target": "goal_worker",
            "reason": "secondary goal worker requested"
        }

    if ("المجدول الذاتي" in text) or ("مجدول ذاتي" in text) or ("scheduler" in text):
        return {
            "ok": True,
            "route": "secondary",
            "system": "autonomous_scheduler",
            "target": "autonomous_scheduler",
            "reason": "secondary autonomous scheduler requested"
        }

    if ("ولد هدف ذاتي" in text) or ("ولّد هدف ذاتي" in text) or ("مولد الأهداف" in text) or ("مولد الاهداف" in text) or ("goal generator" in text):
        return {
            "ok": True,
            "route": "secondary",
            "system": "autonomous_goal_generator",
            "target": "autonomous_goal_generator",
            "reason": "secondary autonomous goal generator requested"
        }

    if ("الحلقة المعرفية" in text) or ("autonomous loop" in text):
        return {
            "ok": True,
            "route": "secondary",
            "system": "autonomous_cognitive_loop",
            "target": "autonomous_cognitive_loop",
            "reason": "secondary autonomous cognitive loop requested"
        }

    if ("البحث المعرفي" in text) or ("cognitive search" in text):
        return {
            "ok": True,
            "route": "secondary",
            "system": "cognitive_search",
            "target": "cognitive_search",
            "reason": "secondary cognitive search requested"
        }

    if any(w in text for w in news_words):
        return {"ok": True, "route": "research", "reason": "news/research goal"}

    if any(w in text for w in android_words):
        return {"ok": True, "route": "android", "reason": "android control goal"}

    if any(w in text for w in memory_words):
        return {"ok": True, "route": "memory", "reason": "memory goal"}

    if any(w in text for w in cognitive_words):
        return {"ok": True, "route": "cognitive", "reason": "thinking/planning goal"}

    return {
        "ok": False,
        "route": None,
        "reason": "no_route_found"
    }
