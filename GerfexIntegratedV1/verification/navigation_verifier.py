import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from android.android_bridge import queue_action
from observation.screen_observer import observe

def verify_navigation(url, expected_terms=None):
    expected_terms = expected_terms or []

    queue_action({
        "action": "open_url",
        "args": {"url": url}
    })

    queue_action({
        "action": "wait",
        "args": {"seconds": 4}
    })

    queue_action({
        "action": "dump_ui",
        "args": {}
    })

    time.sleep(6)

    obs = observe()
    texts = []

    for item in obs.get("items", []):
        text = (item.get("text") or "").strip()
        if text:
            texts.append(text)

    joined = "\n".join(texts).lower()

    signals = {
        "google": "google" in joined,
        "search": "search" in joined or "بحث" in joined,
        "expected_term_found": any(t.lower() in joined for t in expected_terms),
        "old_marsad_page": "صحيفة المرصد" in joined or "آخر الأخبار" in joined
    }

    success = (
        signals["google"]
        or signals["expected_term_found"]
    ) and not signals["old_marsad_page"]

    return {
        "ok": True,
        "navigation_success": success,
        "url": url,
        "top_package": obs.get("top_package"),
        "item_count": obs.get("item_count"),
        "clickable_count": obs.get("clickable_count"),
        "signals": signals,
        "sample_texts": texts[:30]
    }

if __name__ == "__main__":
    url = "https://www.google.com/search?q=%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1+%D8%A7%D9%84%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D9%84%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A"

    result = verify_navigation(
        url,
        expected_terms=[
            "أخبار",
            "الذكاء",
            "الاصطناعي",
            "google"
        ]
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
