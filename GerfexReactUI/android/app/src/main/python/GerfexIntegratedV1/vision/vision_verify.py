import json
from pathlib import Path
from vision.screen_summary import summarize_screen

VERIFY_FILE = Path(__file__).resolve().parent / "last_action_verify.json"

def snapshot():
    s = summarize_screen()
    return {
        "app": s.get("app"),
        "usable": s.get("usable"),
        "dirty": s.get("dirty_termux_dump"),
        "item_count": s.get("item_count"),
        "visible_texts": s.get("visible_texts", [])[:20],
        "top_clickables": s.get("top_clickables", [])[:10]
    }

def compare(before, after):
    before_text = set(before.get("visible_texts", []))
    after_text = set(after.get("visible_texts", []))

    added = list(after_text - before_text)[:20]
    removed = list(before_text - after_text)[:20]

    changed = (
        before.get("app") != after.get("app")
        or before.get("item_count") != after.get("item_count")
        or bool(added)
        or bool(removed)
    )

    return {
        "changed": changed,
        "same_app": before.get("app") == after.get("app"),
        "before_app": before.get("app"),
        "after_app": after.get("app"),
        "before_usable": before.get("usable"),
        "after_usable": after.get("usable"),
        "added_texts": added,
        "removed_texts": removed
    }

def verify(before_file="vision/before_action.json"):
    before_path = Path(before_file)
    if not before_path.exists():
        return {"ok": False, "reason": "missing_before_snapshot"}

    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = snapshot()

    result = {
        "ok": True,
        "before": before,
        "after": after,
        "comparison": compare(before, after)
    }

    VERIFY_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
