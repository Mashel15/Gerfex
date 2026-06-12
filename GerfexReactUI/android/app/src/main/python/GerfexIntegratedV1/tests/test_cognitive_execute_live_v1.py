import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from android.android_bridge import queue_action

action = {
    "action": "open_app",
    "args": {
        "package": "chrome"
    }
}

result = queue_action(action)

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )
)
