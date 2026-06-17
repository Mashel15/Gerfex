import shutil
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

def delete_item(relative_path, line_number=None, recursive=False):
    try:
        p = _safe_path(relative_path)

        if not p.exists():
            return {"ok": False, "reason": "not_found", "path": str(p)}

        if line_number is not None:
            if not p.is_file():
                return {"ok": False, "reason": "line_delete_requires_file"}
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            idx = int(line_number) - 1
            if idx < 0 or idx >= len(lines):
                return {"ok": False, "reason": "line_out_of_range"}
            removed = lines.pop(idx)
            p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            return {"ok": True, "type": "line", "removed": removed, "path": str(p)}

        if p.is_dir():
            if not recursive:
                return {"ok": False, "reason": "folder_delete_requires_recursive_true"}
            shutil.rmtree(p)
            return {"ok": True, "type": "folder", "path": str(p)}

        p.unlink()
        return {"ok": True, "type": "file", "path": str(p)}

    except Exception as e:
        return {"ok": False, "reason": str(e)}
