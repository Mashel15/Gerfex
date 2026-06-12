import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.runtime_state_manager import update_state, get_state

r = update_state({
    "goal": "اختبار الحالة",
    "route": {"route": "test"},
    "intent": "test",
    "target": "runtime",
    "ok": True,
    "error": None
})

assert r["ok"]
s = get_state()
assert s["current_goal"] == "اختبار الحالة"
assert s["status"] == "idle"
assert len(s["history"]) > 0

print("RUNTIME STATE MANAGER V2 OK")
