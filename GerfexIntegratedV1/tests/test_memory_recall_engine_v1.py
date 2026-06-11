import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.unified_memory import remember
from memory.memory_recall import recall

remember({"type": "goal_learning", "goal": "افتح كروم", "target": "chrome", "ok": True})
r = recall("افتح كروم")

assert r["ok"]
assert r["count"] > 0
print("MEMORY RECALL ENGINE V1 OK")
