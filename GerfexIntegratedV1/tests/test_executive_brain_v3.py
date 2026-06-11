import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.gerfex_core import run_goal

goals = [
    "افتح كروم",
    "افتح يوتيوب",
    "افتح الإعدادات",
    "ارجع",
    "الرئيسية",
    "انتظر",
    "تفريغ الشاشة",
]

results = []
for goal in goals:
    result = run_goal(goal)
    results.append(result)
    if result.get("decision", {}).get("brain") != "Queen":
        raise SystemExit(10)
    if not result.get("decision", {}).get("ok"):
        raise SystemExit(1)
    if not result.get("execution", {}).get("ok"):
        raise SystemExit(2)

print(json.dumps(results, ensure_ascii=False, indent=2))
