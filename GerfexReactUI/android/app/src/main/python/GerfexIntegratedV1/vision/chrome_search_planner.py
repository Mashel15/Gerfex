import json
from vision.ui_parser import parse_ui

def find_chrome_url_bar():
    items = parse_ui().get("items", [])

    candidates = []
    for item in items:
        rid = item.get("id") or ""
        hint = item.get("hint") or ""
        cls = item.get("class") or ""

        if rid == "com.android.chrome:id/url_bar":
            candidates.append(item)
        elif "url_bar" in rid:
            candidates.append(item)
        elif "ابحث في Google" in hint or "اكتب عنوان URL" in hint:
            candidates.append(item)

    def score(item):
        s = 0
        if item.get("id") == "com.android.chrome:id/url_bar":
            s += 100
        if item.get("class") == "android.widget.EditText":
            s += 50
        if item.get("clickable"):
            s += 30
        if item.get("focusable"):
            s += 20
        if item.get("center") and item.get("center") != [0, 0]:
            s += 20
        return s

    candidates.sort(key=score, reverse=True)

    best = candidates[0] if candidates else None

    return {
        "ok": bool(best),
        "count": len(candidates),
        "best": best,
        "candidates": candidates[:10]
    }

def plan_chrome_search(query):
    found = find_chrome_url_bar()
    best = found.get("best")

    if not best:
        return {
            "ok": False,
            "reason": "chrome_url_bar_not_found",
            "found": found
        }

    center = best.get("center")
    if not center:
        return {
            "ok": False,
            "reason": "url_bar_has_no_center",
            "found": found
        }

    return {
        "ok": True,
        "query": query,
        "url_bar": {
            "center": center,
            "bounds": best.get("bounds"),
            "text": best.get("text"),
            "hint": best.get("hint"),
            "id": best.get("id")
        },
        "actions": [
            {"action": "tap", "args": {"x": center[0], "y": center[1]}},
            {"action": "wait", "args": {"seconds": 1}},
            {"action": "type_text", "args": {"text": query}},
            {"action": "press_enter", "args": {}},
            {"action": "wait", "args": {"seconds": 3}},
            {"action": "dump_ui", "args": {"focus": "chrome"}}
        ]
    }

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "latest AI news"
    print(json.dumps(plan_chrome_search(q), ensure_ascii=False, indent=2))
