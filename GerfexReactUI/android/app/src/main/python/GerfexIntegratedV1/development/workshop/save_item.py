from pathlib import Path
from gerfex_android_paths import app_path

ROOT = app_path("development", "workshop", "workspace", ".keep").parent

def _safe_path(relative_path):
    rel = str(relative_path or "").strip().lstrip("/")
    if not rel:
        raise ValueError("empty_path")
    p = (ROOT / rel).resolve()
    root = ROOT.resolve()
    if root != p and root not in p.parents:
        raise ValueError("path_outside_workshop")
    return p

def save_item(relative_path, content):
    try:
        p = _safe_path(relative_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(content), encoding="utf-8")
        return {"ok": True, "path": str(p), "bytes": len(str(content).encode("utf-8"))}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
