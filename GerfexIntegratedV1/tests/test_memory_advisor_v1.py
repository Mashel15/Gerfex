import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.memory_advisor import advise

r = advise("افتح كروم", {
    "matches": [
        {"goal": "افتح كروم", "target": "chrome", "ok": True, "route": {"route": "android"}},
        {"goal": "افتح كروم", "target": "chrome", "ok": True, "route": {"route": "android"}},
    ]
})

assert r["ok"]
assert r["recommended_target"] == "chrome"
assert r["recommended_route"] == "android"
assert r["confidence"] == 1.0

print("MEMORY ADVISOR V1 OK")
