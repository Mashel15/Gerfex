import json
from pathlib import Path
from gerfex_android_paths import app_path
from datetime import datetime

LOG = app_path("learning", "executive_learning_log.json")

def learn(goal, decision, execution):
    LOG.parent.mkdir(parents=True, exist_ok=True)

    data = []
    if LOG.exists():
        try:
            data = json.loads(LOG.read_text(encoding="utf-8"))
        except Exception:
            data = []

    event = {
        "time": datetime.utcnow().isoformat() + "Z",
        "goal": goal,
        "decision_ok": decision.get("ok"),
        "intent": decision.get("intent"),
        "target": decision.get("target"),
        "execution_ok": execution.get("ok"),
        "reason": decision.get("reason")
    }

    data.append(event)
    LOG.write_text(json.dumps(data[-300:], ensure_ascii=False, indent=2), encoding="utf-8")
    return event
