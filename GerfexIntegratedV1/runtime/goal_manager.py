import json
from pathlib import Path
from datetime import datetime

QUEUE = Path("runtime/goal_queue.json")

def _now():
    return datetime.utcnow().isoformat() + "Z"

def _load():
    if QUEUE.exists():
        try:
            return json.loads(QUEUE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save(data):
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def add_goal(goal, source="user"):
    data = _load()
    item = {
        "id": f"goal_{len(data)+1}_{int(datetime.utcnow().timestamp())}",
        "goal": goal,
        "source": source,
        "status": "pending",
        "created_at": _now(),
        "started_at": None,
        "finished_at": None,
        "result": None
    }
    data.append(item)
    _save(data)
    return {"ok": True, "goal": item, "count": len(data)}

def list_goals(status=None):
    data = _load()
    if status:
        data = [g for g in data if g.get("status") == status]
    return {"ok": True, "count": len(data), "goals": data}

def next_goal():
    data = _load()
    for g in data:
        if g.get("status") == "pending":
            g["status"] = "running"
            g["started_at"] = _now()
            _save(data)
            return {"ok": True, "goal": g}
    return {"ok": False, "reason": "no_pending_goals"}

def complete_goal(goal_id, result=None):
    data = _load()
    for g in data:
        if g.get("id") == goal_id:
            g["status"] = "completed"
            g["finished_at"] = _now()
            g["result"] = result
            _save(data)
            return {"ok": True, "goal": g}
    return {"ok": False, "reason": "goal_not_found", "id": goal_id}

def fail_goal(goal_id, error=None):
    data = _load()
    for g in data:
        if g.get("id") == goal_id:
            g["status"] = "failed"
            g["finished_at"] = _now()
            g["result"] = {"error": error}
            _save(data)
            return {"ok": True, "goal": g}
    return {"ok": False, "reason": "goal_not_found", "id": goal_id}
