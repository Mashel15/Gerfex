import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vision.ui_parser import parse_ui

OUT = Path("research/last_article_read.json")

BAD_SUBSTRINGS = [
    "android:id/content",
    "com.android.chrome",
    "com.termux",
    "GerfexIntegratedV1",
    "EOF",
    "python -m",
    "Path(",
    "summary",
    "إعلان",
    "root",
    "div-gpt-ad",
    "الاتصال بهذا الموقع الإلكتروني آمن",
    "الاطّلاع على",
    "تخصيص Google Chrome",
    "location_bar",
    "علامات تبويب",

    # tracking / ads / app intent / encoded links
    "intent:",
    "#Intent",
    "Intent;",
    "scheme=market",
    "scheme%3Dmarket",
    "market://",
    "details?id=",
    "details%3Fid",
    "com.openai.chatgpt",
    "gclid",
    "referrer",
    "gref=",
    "play.google",
    "package=com.android",
    "package%3Dcom.android",
    "%3D",
    "%26",
    "%23",
    "http://",
    "https://",
]

BAD_EXACT = {
    "Google",
    "Google Search",
    "Clear Search",
    "Search by voice",
    "AI Mode",
    "All",
    "News",
    "Videos",
    "Images",
    "Shopping",
    "Books",
    "Web",
    "Maps",
    "Flights",
    "Finance",
}


def clean(t):
    return " ".join((t or "").split()).strip()


def is_bad(text):
    if not text:
        return True

    if text in BAD_EXACT:
        return True

    if len(text) < 25:
        return True

    low = text.lower()

    for bad in BAD_SUBSTRINGS:
        if bad.lower() in low:
            return True

    # encoded/tracking-like garbage
    if text.count("%") >= 3:
        return True

    if text.count("&") >= 3 and ("id=" in low or "referrer" in low):
        return True

    return False


def read_article():
    parsed = parse_ui()
    items = parsed.get("items", [])

    raw = json.dumps(parsed, ensure_ascii=False)
    if "com.termux" in raw or "activity_termux" in raw:
        out = {
            "ok": False,
            "reason": "dirty_termux_dump",
            "title": "",
            "paragraphs": []
        }
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return out

    texts = []
    seen = set()

    for item in items:
        text = clean(item.get("text") or item.get("desc") or "")

        if is_bad(text):
            continue

        if text in seen:
            continue

        seen.add(text)
        texts.append(text)

    ok = len(texts) >= 3

    out = {
        "ok": ok,
        "reason": None if ok else "insufficient_article_text",
        "title": texts[0] if texts else "",
        "paragraph_count": max(0, len(texts) - 1),
        "paragraphs": texts[1:30],
        "preview": "\n\n".join(texts[:6])
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(read_article(), ensure_ascii=False, indent=2))
