import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.unified_memory import remember, recent
from learning.unified_learning import learn_from_goal

r = remember({"type": "test", "message": "memory online"})
assert r["ok"]

l = learn_from_goal(
    "اختبار الذاكرة",
    {"route": "test"},
    {"intent": "test", "target": "memory"},
    {"ok": True}
)
assert l["ok"]

assert len(recent(5)) > 0
print("INTEGRATED MEMORY LEARNING V1 OK")
