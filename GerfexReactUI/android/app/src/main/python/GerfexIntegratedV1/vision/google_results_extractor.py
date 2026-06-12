import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pathlib import Path
from vision.ui_parser import parse_ui

OUT = Path(__file__).resolve().parent / "google_results.json"

BAD_KEYWORDS = [
    "Google Account",
    "Google Search",
    "Clear Search",
    "Search by voice",
    "Search tools",
    "Source picker",
    "Short videos",
    "About this result",
    "qslc",
]

KNOWN_SOURCES = [
    "The New York Times",
    "AP News",
    "Reuters",
    "BBC",
    "CNBC",
    "The Verge",
    "TechCrunch",
    "OpenAI",
    "Google",
    "Microsoft",
    "Anthropic",
]

def clean_text(t):
    return " ".join((t or "").split()).strip()

def is_noise(text):
    if not text:
        return True
    if len(text) < 20:
        return True
    return any(bad in text for bad in BAD_KEYWORDS)

def looks_like_result(text, item):
    if is_noise(text):
        return False

    if item.get("clickable") and item.get("focusable") and len(text) > 35:
        return True

    if any(src in text for src in KNOWN_SOURCES) and len(text) > 35:
        return True

    return False

def extract_google_results():
    parsed = parse_ui()
    items = parsed.get("items", [])

    results = []
    seen = set()

    for item in items:
        text = clean_text(item.get("text") or item.get("desc") or "")
        if not looks_like_result(text, item):
            continue

        # تجنب العنوان الداخلي المكرر إذا كان هناك بطاقة clickable كاملة
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "title": text,
            "center": item.get("center"),
            "bounds": item.get("bounds"),
            "clickable": item.get("clickable"),
            "focusable": item.get("focusable"),
            "id": item.get("id"),
            "class": item.get("class")
        })

    out = {
        "ok": True,
        "count": len(results),
        "results": results[:20]
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

if __name__ == "__main__":
    print(json.dumps(extract_google_results(), ensure_ascii=False, indent=2))
