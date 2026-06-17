from urllib.parse import quote_plus

def _search_query(text):
    for marker in ["ابحث عن", "بحث عن", "search for", "search"]:
        if marker in text:
            q = text.split(marker, 1)[1].strip()
            q = q.replace("في كروم", "").replace("على كروم", "").strip()
            return q
    return ""

def ask_queen(goal):
    text = (goal or "").strip().lower()

    q = _search_query(text)
    if q:
        url = "https://www.google.com/search?q=" + quote_plus(q)
        return {
            "intent": "web_search",
            "target": "chrome",
            "actions": [
                {"action": "open_app", "args": {"package": "chrome"}},
                {"action": "wait", "args": {"seconds": 2}},
                {"action": "open_url", "args": {"url": url}},
                {"action": "wait", "args": {"seconds": 3}},
                {"action": "observe_screen", "args": {}}
            ],
            "reason": f"Gerfex قرر فتح كروم والبحث عن: {q}"
        }

    apps = {
        "chrome": ["كروم", "chrome", "المتصفح"],
        "youtube": ["يوتيوب", "youtube"],
        "settings": ["الإعدادات", "اعدادات", "settings"],
    }

    for package, words in apps.items():
        if any(w in text for w in words):
            return {
                "intent": "open_app",
                "target": package,
                "action": {"action": "open_app", "args": {"package": package}},
                "reason": f"Gerfex قرر فتح {package}"
            }

    if "الرئيسية" in text or "home" in text:
        return {"intent":"press_home","target":"android","action":{"action":"press_home","args":{}},"reason":"Gerfex قرر الرجوع للرئيسية"}

    if "ارجع" in text or "back" in text:
        return {"intent":"press_back","target":"android","action":{"action":"press_back","args":{}},"reason":"Gerfex قرر الرجوع للخلف"}

    if "انتظر" in text or "wait" in text:
        return {"intent":"wait","target":"android","action":{"action":"wait","args":{"seconds":2}},"reason":"Gerfex قرر الانتظار"}

    if "صورة الشاشة" in text or "تفريغ الشاشة" in text or "dump" in text:
        return {"intent":"observe_screen","target":"android","action":{"action":"observe_screen","args":{}},"reason":"Gerfex قرر حفظ تفريغ الشاشة"}

    return {"intent":"unknown","target":None,"action":None,"reason":"Gerfex لم يجد قرار تنفيذي آمن"}


def build_search_actions(query):
    url = "https://www.google.com/search?q=" + quote_plus(query)
    return [
        {"action": "open_app", "args": {"package": "chrome"}},
        {"action": "wait", "args": {"seconds": 2}},
        {"action": "open_url", "args": {"url": url}},
        {"action": "wait", "args": {"seconds": 4}},
        {"action": "observe_screen", "args": {}},
    ]


# Compatibility layer for Phase 8
def decide(goal, model_state=None):
    try:
        return queen_decide(goal, model_state)
    except NameError:
        pass
    try:
        return decide_goal(goal, model_state)
    except NameError:
        pass
    try:
        return think(goal, model_state)
    except NameError:
        pass

    text = (goal or "").strip()

    if "ابحث" in text or "بحث" in text:
        from urllib.parse import quote_plus
        q = text
        for w in ["افتح كروم", "افتح", "كروم", "وابحث عن", "ابحث عن", "بحث عن", "ابحث", "بحث"]:
            q = q.replace(w, " ")
        q = " ".join(q.split()) or "أخبار الذكاء الاصطناعي"
        url = "https://www.google.com/search?q=" + quote_plus(q)
        return {
            "ok": True,
            "brain": "Queen",
            "intent": "search_web",
            "target": q,
            "action": None,
            "actions": [
                {"action": "open_app", "args": {"package": "chrome"}},
                {"action": "wait", "args": {"seconds": 2}},
                {"action": "open_url", "args": {"url": url}},
                {"action": "wait", "args": {"seconds": 4}},
                {"action": "observe_screen", "args": {}},
            ],
            "reason": f"Gerfex قرر البحث عن {q}"
        }

    if "يوتيوب" in text:
        target = "youtube"
    elif "الإعدادات" in text or "اعدادات" in text:
        target = "settings"
    else:
        target = "chrome"

    return {
        "ok": True,
        "brain": "Queen",
        "intent": "open_app",
        "target": target,
        "action": {"action": "open_app", "args": {"package": target}},
        "actions": None,
        "reason": f"Gerfex قرر فتح {target}"
    }
