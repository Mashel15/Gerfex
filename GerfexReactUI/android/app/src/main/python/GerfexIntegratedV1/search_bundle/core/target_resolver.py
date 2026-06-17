import json

def resolve_targets(observation, bundle):
    items = observation.get("items", [])

    resolved = []

    for action in bundle.get("action_bundle", []):

        if action.get("action") == "focus_search_box":

            target = None

            # Prefer address/search bar-like items, not generic toolbar buttons.
            candidates = []

            for item in items:
                text = (item.get("text") or "").strip()
                center = item.get("center")
                if not center:
                    continue

                score = 0

                if "." in text or "http" in text.lower():
                    score += 100

                if "search" in text.lower() or "بحث" in text or "google" in text.lower():
                    score += 80

                # Browser address bars are usually near the top and wide.
                bounds = item.get("bounds") or ""
                if "[152,94][871,201]" in bounds:
                    score += 60

                # Avoid obvious toolbar buttons.
                if text in ["أضف للعلامات", "اتصال آمن", "تحديث"]:
                    score -= 100

                if score > 0:
                    candidates.append((score, item))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                target = candidates[0][1]

            if target and target.get("center"):
                x, y = target["center"]

                resolved.append({
                    "action": "tap",
                    "args": {
                        "x": x,
                        "y": y
                    },
                    "resolved_from": "focus_search_box",
                    "reason": "search_box_detected"
                })
            else:
                resolved.append(action)

        else:
            resolved.append(action)

    return {
        "ok": True,
        "resolved_actions": resolved
    }

if __name__ == "__main__":

    observation = {
        "items": [
            {
                "text": "192.168.1.4",
                "center": [511,147]
            }
        ]
    }

    bundle = {
        "action_bundle": [
            {
                "action": "focus_search_box"
            },
            {
                "action": "type_text",
                "args": {
                    "text": "أخبار الذكاء الاصطناعي"
                }
            },
            {
                "action": "press_enter"
            }
        ]
    }

    print(
        json.dumps(
            resolve_targets(observation, bundle),
            ensure_ascii=False,
            indent=2
        )
    )
