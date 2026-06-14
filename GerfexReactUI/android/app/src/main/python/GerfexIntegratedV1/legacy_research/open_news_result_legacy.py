import json, re
from pathlib import Path
from android.android_bridge import queue_action

RESULTS = Path("research/last_news_results.json")

def open_result(command="افتح 1"):
    if not RESULTS.exists():
        return {"ok": False, "reason": "no_saved_news_results"}

    m = re.search(r"\d+", command or "")
    index = int(m.group()) if m else 1

    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    items = data.get("all") or data.get("top") or []

    if index < 1 or index > len(items):
        return {"ok": False, "reason": "index_out_of_range", "count": len(items)}

    item = items[index - 1]
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
        "index": index,
        "title": title,
        "link": link,
        "queued": queued
    }

if __name__ == "__main__":
    import sys
    cmd = " ".join(sys.argv[1:]) or "افتح 1"
    print(json.dumps(open_result(cmd), ensure_ascii=False, indent=2))
