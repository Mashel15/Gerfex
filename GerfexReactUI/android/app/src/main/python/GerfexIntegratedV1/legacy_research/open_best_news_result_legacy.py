import json
from pathlib import Path
from android.android_bridge import queue_action

RESULTS = Path("research/last_news_results.json")

def open_best(open_chrome=True):
    if not RESULTS.exists():
        return {"ok": False, "reason": "no_saved_news_results"}

    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    items = data.get("all") or data.get("top") or []

    candidates = [x for x in items if x.get("readable_candidate")]
    if not candidates:
        return {
            "ok": False,
            "reason": "no_readable_candidate",
            "count": len(items),
            "top_scores": [
                {
                    "title": x.get("title", ""),
                    "score": x.get("source_quality_score"),
                    "domain": x.get("domain")
                }
                for x in items[:5]
            ]
        }

    item = candidates[0]
    link = item.get("link")
    title = item.get("title", "")

    if not link:
        return {"ok": False, "reason": "missing_link", "title": title}

    queued = []
    if open_chrome:
        queued.append(queue_action({"action": "open_app", "args": {"package": "chrome"}}))
    queued.append(queue_action({"action": "wait", "args": {"seconds": 1}}))
    queued.append(queue_action({"action": "open_url", "args": {"url": link}}))
    queued.append(queue_action({"action": "wait", "args": {"seconds": 5}}))
    queued.append(queue_action({"action": "dump_ui", "args": {"focus": "chrome"}}))

    return {
        "ok": True,
        "title": title,
        "link": link,
        "score": item.get("source_quality_score"),
        "domain": item.get("domain"),
        "queued": queued
    }

if __name__ == "__main__":
    print(json.dumps(open_best(), ensure_ascii=False, indent=2))
