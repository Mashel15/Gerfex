import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation.screen_observer import observe

PACKAGE_TYPES = {
    "com.sec.android.app.sbrowser": {
        "screen_type": "browser",
        "summary": "Samsung Internet browser",
        "capabilities": ["navigate", "search", "open_url", "read_page"],
        "confidence": 0.95
    },
    "com.android.chrome": {
        "screen_type": "browser",
        "summary": "Google Chrome browser",
        "capabilities": ["navigate", "search", "open_url", "read_page"],
        "confidence": 0.95
    },
    "com.google.android.youtube": {
        "screen_type": "youtube",
        "summary": "YouTube application",
        "capabilities": ["search_video", "play_video", "navigate"],
        "confidence": 0.95
    },
    "com.android.settings": {
        "screen_type": "settings",
        "summary": "Android Settings",
        "capabilities": ["navigate_settings", "toggle_settings"],
        "confidence": 0.95
    }
}

def understand_screen(observation=None):
    obs = observation or observe()

    if not obs.get("ok"):
        return {
            "ok": False,
            "reason": obs.get("reason", "observation_failed"),
            "observation": obs
        }

    package = obs.get("top_package")
    base = PACKAGE_TYPES.get(package)

    if base:
        return {
            "ok": True,
            "top_package": package,
            **base,
            "item_count": obs.get("item_count", 0),
            "clickable_count": obs.get("clickable_count", 0),
            "observation": obs
        }

    return {
        "ok": True,
        "top_package": package,
        "screen_type": "unknown",
        "summary": f"Unknown screen package: {package}",
        "capabilities": ["observe_only"],
        "confidence": 0.35,
        "item_count": obs.get("item_count", 0),
        "clickable_count": obs.get("clickable_count", 0),
        "observation": obs
    }

if __name__ == "__main__":
    print(json.dumps(understand_screen(), ensure_ascii=False, indent=2))
