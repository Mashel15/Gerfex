import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.gerfex_core import run_goal

goal = " ".join(sys.argv[1:]) or "افتح كروم"
result = run_goal(goal)

print(json.dumps(result, ensure_ascii=False, indent=2))

if result.get("decision", {}).get("brain") != "Queen":
    raise SystemExit(10)

if not result.get("decision", {}).get("ok"):
    raise SystemExit(1)

if not result.get("execution", {}).get("ok"):
    raise SystemExit(2)
