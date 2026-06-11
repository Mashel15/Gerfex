import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from android.android_bridge import queue_action
from observation.screen_observer import observe


def dump_and_check():

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

    joined = "\n".join(texts)

    return {
        "top_package": obs.get("top_package"),
        "texts": texts[:50],
        "joined": joined
    }


def verify_search_page(data):

    joined = data["joined"]

    if "صحيفة المرصد" in joined:
        return False

    if "آخر الأخبار" in joined:
        return False

    return True


def recover_navigation(url):

    attempts = []

    for attempt in range(1, 4):

        queue_action({
            "action": "open_url",
            "args": {"url": url}
        })

        result = dump_and_check()

        ok = verify_search_page(result)

        attempts.append({
            "attempt": attempt,
            "success": ok,
            "top_package": result["top_package"]
        })

        if ok:
            return {
                "ok": True,
                "recovered": True,
                "attempts": attempts
            }

        queue_action({
            "action": "press_home",
            "args": {}
        })

        queue_action({
            "action": "wait",
            "args": {"seconds": 2}
        })

    return {
        "ok": False,
        "recovered": False,
        "attempts": attempts
    }


if __name__ == "__main__":

    url = "https://www.google.com/search?q=%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1+%D8%A7%D9%84%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D9%84%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A"

    print(
        json.dumps(
            recover_navigation(url),
            ensure_ascii=False,
            indent=2
        )
    )
