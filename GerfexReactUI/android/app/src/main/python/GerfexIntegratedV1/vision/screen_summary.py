import json
from pathlib import Path
from vision.screen_analyzer import analyze_screen

SUMMARY_FILE = Path(__file__).resolve().parent / "screen_summary.json"

def summarize_screen():
    analysis = analyze_screen()
    items = analysis.get("top_items", [])

    texts = []
    clickables = []

    for item in items:
        label = (item.get("text") or item.get("desc") or item.get("id") or "").strip()
        if not label:
            continue

        clean = " ".join(label.split())
        if clean and clean not in texts:
            texts.append(clean)

        if item.get("clickable"):
            clickables.append({
                "label": clean,
                "center": item.get("center"),
                "bounds": item.get("bounds")
            })

    result = {
        "ok": analysis.get("ok", False),
        "app": analysis.get("app_guess", "unknown"),
        "usable": analysis.get("usable_for_app_understanding", False),
        "dirty_termux_dump": analysis.get("dirty_termux_dump", False),
        "item_count": analysis.get("item_count", 0),
        "visible_texts": texts[:40],
        "clickable_count": len(clickables),
        "top_clickables": clickables[:25]
    }

    SUMMARY_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(summarize_screen(), ensure_ascii=False, indent=2))
