import json
from pathlib import Path
from gerfex_android_paths import app_path
from datetime import datetime

MEM = app_path("memory", "gerfex_unified_memory.json")

def _load():
    if MEM.exists():
        try:
            return json.loads(MEM.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def remember(event):
    MEM.parent.mkdir(parents=True, exist_ok=True)
    data = _load()
    event["time"] = datetime.utcnow().isoformat() + "Z"
    data.append(event)
    MEM.write_text(json.dumps(data[-500:], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "memory_file": str(MEM), "count": len(data[-500:])}

def recent(limit=20):
    return _load()[-limit:]
