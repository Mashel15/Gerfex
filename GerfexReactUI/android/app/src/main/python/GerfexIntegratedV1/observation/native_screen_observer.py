import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gerfex_android_paths import app_path

SCREEN_TEXT_FILE = app_path("runtime", "native_screen_text.txt")

def observe_native_text(path=SCREEN_TEXT_FILE):
    p = app_path("runtime", "native_screen_text.txt")
    if not p.exists():
        return {
            "ok": False,
            "source": "native_accessibility_text",
            "reason": "native_screen_text_missing",
            "path": str(p),
            "top_package": None,
            "item_count": 0,
            "clickable_count": 0,
            "items": []
        }

    raw = p.read_text(encoding="utf-8", errors="ignore")
    lines = [x.strip() for x in raw.splitlines() if x.strip()]

    items = [
        {
            "text": line,
            "clickable": False,
            "bounds": "",
            "center": None,
            "package": "android_accessibility"
        }
        for line in lines[:80]
    ]

    return {
        "ok": True,
        "source": "native_accessibility_text",
        "path": str(p),
        "top_package": "android_accessibility",
        "item_count": len(items),
        "clickable_count": 0,
        "items": items
    }

if __name__ == "__main__":
    import json
    print(json.dumps(observe_native_text(), ensure_ascii=False, indent=2))
