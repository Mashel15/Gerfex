import json
from pathlib import Path
from datetime import datetime

STATE = Path("runtime/runtime_state.json")

def _now():
    return datetime.utcnow().isoformat() + "Z"

def _load():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def update_state(event):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = _load()

    history = state.get("history", [])
    history.append({
        "time": _now(),
        "goal": event.get("goal"),
        "route": event.get("route"),
        "intent": event.get("intent"),
        "target": event.get("target"),
        "ok": event.get("ok"),
        "error": event.get("error")
    })

    state.update({
        "ok": True,
        "updated_at": _now(),
        "current_goal": event.get("goal"),
        "current_route": event.get("route"),
        "current_intent": event.get("intent"),
        "current_target": event.get("target"),
        "last_ok": event.get("ok"),
        "last_error": event.get("error"),
        "status": "idle" if event.get("ok") else "error",
        "history": history[-100:]
    })

    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "state_file": str(STATE), "status": state["status"]}

def get_state():
    return _load()
