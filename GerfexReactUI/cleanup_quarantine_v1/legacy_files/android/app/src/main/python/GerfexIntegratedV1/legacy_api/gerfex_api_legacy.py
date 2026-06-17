import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from pydantic import BaseModel

from core.gerfex_core import run_goal
from runtime.runtime_state_manager import get_state
from runtime.goal_manager import list_goals

app = FastAPI(title="Gerfex Integrated API", version="1.0")

class ThinkRequest(BaseModel):
    prompt: str
    model: str | None = None

class AndroidActionRequest(BaseModel):
    action: str
    args: dict = {}

@app.get("/")
def root():
    return {
        "ok": True,
        "name": "Gerfex",
        "mode": "integrated_core",
        "brain": "provider_slot",
        "note": "API talks to Gerfex Core, not Queen directly"
    }

@app.get("/status")
def status():
    return {
        "ok": True,
        "state": get_state(),
        "goals": list_goals()
    }

@app.post("/think")
def think(req: ThinkRequest):
    result = run_goal(req.prompt)
    return {
        "ok": True,
        "input": req.prompt,
        "model": req.model,
        "result": result
    }

@app.get("/runtime/state")
def runtime_state():
    return {
        "ok": True,
        "state": get_state()
    }

@app.get("/goals")
def goals():
    return list_goals()

@app.post("/android/action")
def android_action(req: AndroidActionRequest):
    from android.android_bridge import queue_action
    from safety.safety_guard import check_action

    action = {"action": req.action, "args": req.args}
    safety = check_action(action)
    if not safety.get("ok"):
        return {"ok": False, "reason": "blocked_by_safety", "safety": safety}

    queued = queue_action(action)
    return {"ok": True, "queued": queued}
