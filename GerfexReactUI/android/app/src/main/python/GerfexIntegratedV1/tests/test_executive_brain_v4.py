import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.gerfex_core import run_goal

goal = "افتح كروم وابحث عن أخبار الذكاء الاصطناعي"
result = run_goal(goal)

print(json.dumps(result, ensure_ascii=False, indent=2))

if result.get("decision", {}).get("brain") != "Queen":
    raise SystemExit(10)

if result.get("decision", {}).get("intent") != "web_search":
    raise SystemExit(11)

if not result.get("decision", {}).get("actions"):
    raise SystemExit(12)

if result.get("execution", {}).get("queued_count", 0) < 3:
    raise SystemExit(13)

if not result.get("execution", {}).get("ok"):
    raise SystemExit(2)
