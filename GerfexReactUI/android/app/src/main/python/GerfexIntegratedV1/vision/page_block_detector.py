import json
from vision.ui_parser import parse_ui

BLOCK_WORDS = [
    "sign in",
    "subscribe",
    "log in",
    "login",
    "register",
    "google-one-tap",
    "one tap",
    "اشترك",
    "سجل",
    "تسجيل",
    "الدخول",
]

def detect_blocked_page():
    items = parse_ui().get("items", [])
    text = " ".join(
        (i.get("text") or "") + " " + (i.get("desc") or "") + " " + (i.get("id") or "")
        for i in items
    ).lower()

    hits = [w for w in BLOCK_WORDS if w.lower() in text]

    return {
        "ok": True,
        "blocked": bool(hits),
        "hits": hits,
        "item_count": len(items)
    }

if __name__ == "__main__":
    print(json.dumps(detect_blocked_page(), ensure_ascii=False, indent=2))
