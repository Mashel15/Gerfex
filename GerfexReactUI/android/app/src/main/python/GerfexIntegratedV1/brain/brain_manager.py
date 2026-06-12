import json
from pathlib import Path

MEMORY = Path("memory/brain_memory.json")

def remember(event):
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    data = []
    if MEMORY.exists():
        try:
            data = json.loads(MEMORY.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append(event)
    MEMORY.write_text(json.dumps(data[-200:], ensure_ascii=False, indent=2), encoding="utf-8")

def decide(goal):
    try:
        from brain.providers.queen_provider import ask_queen
        q = ask_queen(goal)

        actions = q.get("actions")
        action = q.get("action")
        ok = bool(actions or action)

        return {
            "ok": ok,
            "brain": "Queen",
            "intent": q.get("intent", "unknown"),
            "target": q.get("target"),
            "action": action,
            "actions": actions,
            "reason": q.get("reason", "Queen decision")
        }

    except Exception as e:
        return {
            "ok": False,
            "brain": "Queen",
            "intent": "error",
            "target": None,
            "action": None,
            "actions": None,
            "reason": f"Queen provider error: {e}"
        }
