def plan_action(prompt, intent=None):
    text = (prompt or "").strip().lower()

    if intent != "android_action_request":
        return None

    if "كروم" in text or "chrome" in text:
        return {
            "action": "open_app",
            "args": {
                "package": "chrome"
            }
        }

    if "يوتيوب" in text or "youtube" in text:
        return {
            "action": "open_app",
            "args": {
                "package": "youtube"
            }
        }

    if "الإعدادات" in text or "اعدادات" in text or "settings" in text:
        return {
            "action": "open_app",
            "args": {
                "package": "settings"
            }
        }

    if "ارجع" in text:
        return {
            "action": "press_back",
            "args": {}
        }

    if "الرئيسية" in text:
        return {
            "action": "press_home",
            "args": {}
        }

    return {
        "action": "dump_ui",
        "args": {}
    }
