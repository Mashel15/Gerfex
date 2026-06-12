import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.providers.queen_provider import decide

r = decide("افتح كروم وابحث عن أخبار الذكاء الاصطناعي")
assert r["ok"]
assert r["intent"] == "search_web"
assert isinstance(r.get("actions"), list)
assert len(r["actions"]) >= 3
assert r["actions"][0]["action"] == "open_app"
assert any(a["action"] == "open_url" for a in r["actions"])
print("MULTI STEP EXECUTION V1 OK")
