from GerfexIntegratedV1.development.workshop.save_item import save_item
from GerfexIntegratedV1.development.workshop.open_item import open_item

def run_basic_test():
    test_path = "__tests__/basic_test.txt"
    expected = "Gerfex workshop test OK"

    saved = save_item(test_path, expected)
    if not saved.get("ok"):
        return {"ok": False, "stage": "save", "result": saved}

    opened = open_item(test_path)
    if not opened.get("ok"):
        return {"ok": False, "stage": "open", "result": opened}

    actual = opened.get("content", "")
    return {
        "ok": actual == expected,
        "stage": "done",
        "expected": expected,
        "actual": actual,
        "path": test_path
    }
