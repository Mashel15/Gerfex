import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cognitive.action_selector import select_action
from planner.action_planner import create_plan

u = {
    "screen_type": "browser",
    "capabilities": ["navigate", "search", "open_url", "read_page"]
}

r = select_action("حلل الشاشة الحالية", {"understanding": u})
assert r["ok"]
assert r["action"] == "read_page"

p = create_plan("حلل الشاشة الحالية", u)
assert p["ok"]
assert p["action"] == "read_page"
assert p["source"] == "ActionSelectorV1"

print("ACTION SELECTOR LINK V1 OK")
