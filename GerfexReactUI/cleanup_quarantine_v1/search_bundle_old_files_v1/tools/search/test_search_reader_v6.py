import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from perception.search_reader import extract_search_results

result = extract_search_results(limit=10)
print(json.dumps(result, ensure_ascii=False, indent=2))

if not result.get("ok"):
    raise SystemExit(1)

if result.get("count", 0) == 0:
    raise SystemExit(2)
