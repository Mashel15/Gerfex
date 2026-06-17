from vision.target_finder import find_target

def plan_tap_target(query):
    found = find_target(query)
    best = found.get("best")

    if not best:
        return {
            "ok": False,
            "reason": "target_not_found",
            "query": query,
            "action": None
        }

    if not best.get("clickable"):
        return {
            "ok": False,
            "reason": "target_not_clickable",
            "query": query,
            "target": best,
            "action": None
        }

    center = best.get("center")
    if not center:
        return {
            "ok": False,
            "reason": "target_has_no_center",
            "query": query,
            "target": best,
            "action": None
        }

    return {
        "ok": True,
        "query": query,
        "target": best,
        "action": {
            "action": "tap",
            "args": {
                "x": center[0],
                "y": center[1]
            }
        }
    }

if __name__ == "__main__":
    import sys, json
    q = " ".join(sys.argv[1:]) or "بحث"
    print(json.dumps(plan_tap_target(q), ensure_ascii=False, indent=2))
