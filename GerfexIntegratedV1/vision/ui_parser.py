import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

UI_XML = Path("/sdcard/Download/gerfex_ui.xml")
STATE_FILE = Path(__file__).resolve().parent / "screen_state.json"

def bounds_center(bounds):
    nums = list(map(int, re.findall(r"\d+", bounds or "")))
    if len(nums) != 4:
        return None
    x1, y1, x2, y2 = nums
    return [(x1 + x2) // 2, (y1 + y2) // 2]

def parse_ui(path=UI_XML):
    if not Path(path).exists():
        return {"ok": False, "error": f"missing_ui_xml:{path}", "items": []}

    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}

    items = []
    for node in root.iter("node"):
        text = node.attrib.get("text", "") or ""
        desc = node.attrib.get("content-desc", "") or ""
        rid = node.attrib.get("resource-id", "") or ""
        cls = node.attrib.get("class", "") or ""
        hint = node.attrib.get("hint", "") or ""
        clickable = node.attrib.get("clickable", "false")
        focusable = node.attrib.get("focusable", "false")
        focused = node.attrib.get("focused", "false")
        bounds = node.attrib.get("bounds", "")

        label = text or desc or rid or hint or cls
        if not label:
            continue

        items.append({
            "text": text,
            "desc": desc,
            "id": rid,
            "class": cls,
            "hint": hint,
            "clickable": clickable == "true",
            "focusable": focusable == "true",
            "focused": focused == "true",
            "bounds": bounds,
            "center": bounds_center(bounds)
        })

    result = {"ok": True, "source": str(path), "count": len(items), "items": items}
    STATE_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(parse_ui(), ensure_ascii=False, indent=2))
