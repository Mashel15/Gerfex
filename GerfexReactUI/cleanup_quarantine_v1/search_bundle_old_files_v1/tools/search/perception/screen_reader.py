import json
import xml.etree.ElementTree as ET
from pathlib import Path

UI_FILE = Path("runtime/last_ui.xml")

def read_screen(path=UI_FILE):
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "ui_file_missing", "items": []}

    root = ET.fromstring(p.read_text(encoding="utf-8", errors="ignore"))

    items = []
    for node in root.iter("node"):
        text = (node.attrib.get("text") or "").strip()
        desc = (node.attrib.get("content-desc") or "").strip()
        rid = (node.attrib.get("resource-id") or "").strip()
        clickable = node.attrib.get("clickable") == "true"
        bounds = node.attrib.get("bounds", "")

        label = text or desc
        if not label:
            continue

        items.append({
            "text": label,
            "resource_id": rid,
            "clickable": clickable,
            "bounds": bounds
        })

    return {
        "ok": True,
        "count": len(items),
        "items": items[:80]
    }

if __name__ == "__main__":
    print(json.dumps(read_screen(), ensure_ascii=False, indent=2))
