import json
from pathlib import Path

MEM = Path("memory/gerfex_unified_memory.json")

def _load():
    if not MEM.exists():
        return []
    try:
        return json.loads(MEM.read_text(encoding="utf-8"))
    except Exception:
        return []

def recall(goal, limit=5):
    goal = (goal or "").strip()
    data = _load()
    matches = []

    for item in reversed(data):
        old_goal = str(item.get("goal", ""))
        if goal and (goal in old_goal or old_goal in goal):
            matches.append(item)
        elif item.get("target") and item.get("target") in goal:
            matches.append(item)

        if len(matches) >= limit:
            break

    return {
        "ok": True,
        "goal": goal,
        "count": len(matches),
        "matches": matches
    }
