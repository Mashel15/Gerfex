import json
from math import hypot
from vision.ui_parser import parse_ui

SEARCH_WORDS = ["بحث", "search", "find"]
SEARCH_ICONS = ["", "🔍", "⌕"]

def label_of(item):
    return (item.get("text") or item.get("desc") or item.get("id") or "").strip()

def is_search_like(label):
    low = (label or "").lower()
    return any(w in low for w in SEARCH_WORDS) or any(i in label for i in SEARCH_ICONS)

def dist(a, b):
    if not a or not b:
        return 999999
    return hypot(a[0] - b[0], a[1] - b[1])

def find_semantic_target(role):
    parsed = parse_ui()
    items = parsed.get("items", [])

    role = (role or "").strip().lower()
    candidates = []

    for item in items:
        label = label_of(item)
        if role in ["search", "بحث"] and is_search_like(label):
            candidates.append({
                "label": label,
                "clickable": item.get("clickable"),
                "center": item.get("center"),
                "bounds": item.get("bounds"),
                "id": item.get("id"),
                "reason": "direct_search_match"
            })

    # إذا وجدنا أيقونة بحث غير قابلة للضغط، ابحث عن أقرب عنصر clickable حولها
    expanded = list(candidates)
    for c in candidates:
        if c.get("clickable"):
            continue

        cc = c.get("center")
        nearest = None
        nearest_d = 999999

        for item in items:
            if not item.get("clickable"):
                continue
            d = dist(cc, item.get("center"))
            if d < nearest_d and d <= 90:
                nearest_d = d
                nearest = item

        if nearest:
            expanded.append({
                "label": label_of(nearest) or c.get("label"),
                "clickable": True,
                "center": nearest.get("center"),
                "bounds": nearest.get("bounds"),
                "id": nearest.get("id"),
                "reason": f"nearest_clickable_to_search_icon:{int(nearest_d)}px"
            })

    def score(c):
        s = 0
        label = c.get("label") or ""
        if c.get("clickable"):
            s += 100
        if "بحث" in label or "search" in label.lower():
            s += 80
        if any(i in label for i in SEARCH_ICONS):
            s += 50
        if c.get("center") and c.get("center") != [0, 0]:
            s += 30
        if c.get("bounds") and c.get("bounds") != "[0,0][0,0]":
            s += 20
        if "nearest_clickable" in c.get("reason", ""):
            s += 10
        return s

    expanded.sort(key=score, reverse=True)

    return {
        "ok": True,
        "role": role,
        "count": len(expanded),
        "candidates": expanded[:20],
        "best": expanded[0] if expanded else None
    }

if __name__ == "__main__":
    import sys
    role = " ".join(sys.argv[1:]) or "search"
    print(json.dumps(find_semantic_target(role), ensure_ascii=False, indent=2))
