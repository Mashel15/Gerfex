import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vision.google_results_extractor import extract_google_results
from android.android_bridge import queue_action
from safety.safety_guard import check_action

OUT = Path("vision/google_best_result.json")

BAD = [
    "Google Search", "Google Account", "View related links",
    "Instagram", "play.google", "صور", "فيديوهات"
]

def good(r):
    title = (r.get("title") or "").strip()
    x, y = r.get("center") or [0, 0]
    if not title or len(title) < 20:
        return False
    if any(b.lower() in title.lower() for b in BAD):
        return False
    if not r.get("clickable"):
        return False
    if x <= 0 or y <= 0:
        return False
    if y >= 2100:
        return False
    return True

def open_best():
    data = extract_google_results()
    results = data.get("results", [])
    candidates = [r for r in results if good(r)]

    if not candidates:
        out = {"ok": False, "reason": "no_visible_clickable_result", "count": len(results)}
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return out

    best = candidates[0]
    x, y = best["center"]

    actions = [
        {"action": "open_app", "args": {"package": "chrome"}},
        {"action": "wait", "args": {"seconds": 1}},
        {"action": "tap", "args": {"x": int(x), "y": int(y)}},
        {"action": "wait", "args": {"seconds": 5}},
        {"action": "dump_ui", "args": {"focus": "chrome"}},
    ]

    queued = []
    for a in actions:
        safety = check_action(a)
        if not safety.get("allowed"):
            queued.append({"ok": False, "blocked": True, "action": a, "safety": safety})
            continue
        queued.append(queue_action(a))

    out = {"ok": True, "best": best, "queued": queued}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

if __name__ == "__main__":
    print(json.dumps(open_best(), ensure_ascii=False, indent=2))
