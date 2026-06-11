SAFE_ACTIONS = {
    "open_app",
    "open_url",
    "tap",
    "swipe",
    "type_text",
    "press_back",
    "press_home",
    "press_recent",
    "wait",
    "dump_ui"
}

HIGH_RISK_ACTIONS = {
    "delete_file",
    "format",
    "factory_reset",
    "install_apk",
    "uninstall_app",
    "send_message",
    "purchase"
}

def check_action(action):
    if not action:
        return {
            "allowed": False,
            "reason": "no_action"
        }

    name = action.get("action")

    if name in HIGH_RISK_ACTIONS:
        return {
            "allowed": False,
            "reason": "high_risk_requires_explicit_confirmation"
        }

    if name not in SAFE_ACTIONS:
        return {
            "allowed": False,
            "reason": f"unknown_or_disallowed_action:{name}"
        }

    return {
        "allowed": True,
        "reason": "safe_action"
    }
