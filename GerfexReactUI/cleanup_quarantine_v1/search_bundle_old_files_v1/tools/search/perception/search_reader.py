import json
from perception.screen_reader import read_screen

BAD = {
    "google", "google search", "clear search", "search by voice",
    "ai mode", "all", "news", "videos", "images", "short videos",
    "shopping", "books", "web", "maps", "flights", "finance",
    "search tools", "feedback", "search results", "web results",
    "about this result", "view related links", "show more ai overview",
    "source picker options"
}

def is_zero_bounds(bounds):
    return bounds.strip() == "[0,0][0,0]"

def clean_text(t):
    return " ".join((t or "").replace("\n", " ").split())

def extract_search_results(limit=10):
    screen = read_screen()
    if not screen.get("ok"):
        return {"ok": False, "reason": screen.get("reason"), "results": []}

    results = []
    seen = set()

    for item in screen.get("items", []):
        text = clean_text(item.get("text"))
        if not text:
            continue

        low = text.lower()
        if low in BAD:
            continue

        if is_zero_bounds(item.get("bounds", "")):
            continue

        if len(text) < 8:
            continue

        ui_noise = [
            "google search", "google account", "أخبار الذكاء الاصطناعي - google search",
            "أخبار الذكاء الاصطناعي", "ai overview", "view 3 corroboration links",
            "view related links"
        ]
        if low in ui_noise or any(x in low for x in ["google account", "corroboration"]):
            continue

        if text.startswith("تشهد ساحة") or text.startswith("، حيث"):
            continue

        if low in ["2 hours ago", "5 hours ago", "43 minutes ago", "50 minutes ago", "سكاي نيوز عربية"]:
            continue

        if low.startswith("http") and len(text) < 40:
            continue

        if text.startswith("العربية (+"):
            continue

        useful = (
            "http" in low
            or ("ago" in low and len(text) > 25)
            or ("منذ" in text and len(text) > 25)
            or any(src in text for src in ["العربية", "سكاي", "إرم", "عكاظ", "Investing", "Jawlah", "موقع 24"])
        )
        if not useful:
            continue

        key = text[:120]
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "title": text,
            "clickable": item.get("clickable", False),
            "bounds": item.get("bounds", "")
        })

        if len(results) >= limit:
            break

    return {
        "ok": True,
        "count": len(results),
        "results": results
    }

if __name__ == "__main__":
    print(json.dumps(extract_search_results(), ensure_ascii=False, indent=2))
