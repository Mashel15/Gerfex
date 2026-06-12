import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.experience_decision import apply_experience_advice

d = {"ok": True, "intent": "open_app", "target": None}
m = {"ok": True, "recommended_route": "android", "recommended_target": "chrome", "confidence": 0.9}

r = apply_experience_advice("افتح كروم", d, m)

assert r["experience_used"] is True
assert r["target"] == "chrome"
assert r["experience_route"] == "android"

print("EXPERIENCE DECISION V1 OK")
