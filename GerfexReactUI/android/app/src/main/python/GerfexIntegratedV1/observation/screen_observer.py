import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

UI_PATH = Path("/sdcard/Download/gerfex_ui.xml")

def center_from_bounds(bounds):
    nums = [int(x) for x in re.findall(r"\d+", bounds or "")]
    if len(nums) != 4:
        return None
    x1, y1, x2, y2 = nums
    return [(x1 + x2) // 2, (y1 + y2) // 2]

def observe(path=UI_PATH):
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "ui_dump_missing", "path": str(p)}

    root = ET.fromstring(p.read_text(encoding="utf-8", errors="ignore"))

    items = []
    packages = {}

    for node in root.iter("node"):
        package = node.attrib.get("package", "")
        if package:
            packages[package] = packages.get(package, 0) + 1

        text = (node.attrib.get("text") or "").strip()
        desc = (node.attrib.get("content-desc") or "").strip()
        label = text or desc

        if not label:
            continue

        bounds = node.attrib.get("bounds", "")
        items.append({
            "text": label,
            "clickable": node.attrib.get("clickable") == "true",
            "bounds": bounds,
            "center": center_from_bounds(bounds),
            "package": package
        })

    top_package = max(packages, key=packages.get) if packages else None

    return {
        "ok": True,
        "path": str(p),
        "top_package": top_package,
        "item_count": len(items),
        "clickable_count": sum(1 for x in items if x["clickable"]),
        "items": items[:40]
    }

if __name__ == "__main__":
    print(json.dumps(observe(), ensure_ascii=False, indent=2))
