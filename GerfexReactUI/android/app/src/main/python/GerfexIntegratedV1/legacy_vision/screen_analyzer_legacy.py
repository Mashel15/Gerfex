import json
from pathlib import Path
from vision.ui_parser import parse_ui

STATE_FILE = Path(__file__).resolve().parent / "screen_analysis.json"

def analyze_screen():
    parsed = parse_ui()
    items = parsed.get("items", [])

    ids = " ".join((x.get("id") or "") for x in items).lower()
    texts = " ".join((x.get("text") or "") + " " + (x.get("desc") or "") for x in items).lower()

    dirty_termux = (
        "com.termux" in ids
        or "termux" in texts
        or "terminal_view" in ids
        or "esc" in texts
    )

    app_guess = "unknown"
    if "com.android.chrome" in ids:
        app_guess = "chrome"
    elif "com.google.android.youtube" in ids:
        app_guess = "youtube"
    elif "com.termux" in ids:
        app_guess = "termux"

    result = {
        "ok": parsed.get("ok", False),
        "app_guess": app_guess,
        "dirty_termux_dump": dirty_termux,
        "usable_for_app_understanding": bool(parsed.get("ok")) and not dirty_termux,
        "item_count": parsed.get("count", 0),
        "top_items": items[:20]
    }

    STATE_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(analyze_screen(), ensure_ascii=False, indent=2))
