import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from perception.screen_reader import read_screen

result = read_screen()
print(json.dumps(result, ensure_ascii=False, indent=2))

if not result.get("ok"):
    raise SystemExit(1)

if result.get("count", 0) == 0:
    raise SystemExit(2)
