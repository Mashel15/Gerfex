import json, time
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "runtime_state.json"

DEFAULT_STATE = {
    "version": "GERFEX_RUNTIME_STATE_V1",
    "status": "active",
    "started_at": time.time(),
    "updated_at": time.time(),
    "current_goal": None,
    "last_user_command": None,
    "last_model": None,
    "last_decision": None,
    "last_reply": None,
    "last_queued_action": None,
    "last_runner_action": None,
    "last_runner_result": None,
    "last_error": None,
    "counters": {
        "think_calls": 0,
        "queued_actions": 0,
        "runner_actions": 0,
        "errors": 0
    },
    "history": []
}

def load_state():
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return dict(DEFAULT_STATE)

def save_state(state):
    state["updated_at"] = time.time()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state

def record(event, **data):
    state = load_state()
    state["status"] = data.pop("status", state.get("status", "active"))

    counters = state.setdefault("counters", {})
    if event == "think":
        counters["think_calls"] = counters.get("think_calls", 0) + 1
    elif event == "queued_action":
        counters["queued_actions"] = counters.get("queued_actions", 0) + 1
    elif event == "runner_action":
        counters["runner_actions"] = counters.get("runner_actions", 0) + 1
    elif event == "error":
        counters["errors"] = counters.get("errors", 0) + 1

    for k, v in data.items():
        if k in state:
            state[k] = v

    history = state.setdefault("history", [])
    history.append({
        "time": time.time(),
        "event": event,
        "data": data
    })
    state["history"] = history[-80:]

    return save_state(state)
