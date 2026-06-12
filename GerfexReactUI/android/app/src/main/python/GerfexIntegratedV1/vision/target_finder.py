import json
from vision.ui_parser import parse_ui

def score_item(label, item, query):
    q = (query or "").strip().lower()
    low = (label or "").strip().lower()
    bounds = item.get("bounds") or ""
    center = item.get("center")

    score = 0

    if low == q:
        score += 100
    elif q in low:
        score += 50

    if item.get("clickable"):
        score += 30

    if center and center != [0, 0]:
        score += 20

    if bounds and bounds != "[0,0][0,0]":
        score += 10

    if item.get("id"):
        score += 5

    # قلل نقاط الرموز/الأيقونات الغامضة
    if len(low) <= 1:
        score -= 20

    return score

def find_target(query):
    q = (query or "").strip().lower()
    parsed = parse_ui()
    items = parsed.get("items", [])

    matches = []
    for item in items:
        labels = [
            item.get("text") or "",
            item.get("desc") or "",
            item.get("id") or "",
        ]

        label = next((x.strip() for x in labels if x and x.strip()), "")
        if not label:
            continue

        low = label.lower()
        if q in low:
            m = {
                "label": label,
                "clickable": item.get("clickable"),
                "center": item.get("center"),
                "bounds": item.get("bounds"),
                "id": item.get("id"),
            }
            m["score"] = score_item(label, item, query)
            matches.append(m)

    matches.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "ok": True,
        "query": query,
        "count": len(matches),
        "matches": matches[:30],
        "best": matches[0] if matches else None
    }

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "بحث"
    print(json.dumps(find_target(q), ensure_ascii=False, indent=2))
