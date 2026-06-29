from pathlib import Path
from GerfexIntegratedV1.gerfex_android_paths import app_path

ROOT = app_path("development", "workshop", "workspace", ".keep").parent

def _safe_path(relative_path=""):
    rel = str(relative_path or "").strip().lstrip("/")
    p = (ROOT / rel).resolve()
    root = ROOT.resolve()
    if root != p and root not in p.parents:
        raise ValueError("path_outside_workshop")
    return p

def open_item(relative_path=""):
    try:
        p = _safe_path(relative_path)
        ROOT.mkdir(parents=True, exist_ok=True)

        if not p.exists():
            return {"ok": False, "reason": "not_found", "path": str(p)}

        if p.is_dir():
            items = []
            for x in sorted(p.iterdir(), key=lambda v: (not v.is_dir(), v.name.lower())):
                items.append({
                    "name": x.name,
                    "type": "folder" if x.is_dir() else "file",
                    "path": str(x.relative_to(ROOT))
                })
            return {"ok": True, "type": "folder", "path": str(p), "items": items}

        text = p.read_text(encoding="utf-8", errors="replace")
        return {"ok": True, "type": "file", "path": str(p), "content": text}

    except Exception as e:
        return {"ok": False, "reason": str(e)}
