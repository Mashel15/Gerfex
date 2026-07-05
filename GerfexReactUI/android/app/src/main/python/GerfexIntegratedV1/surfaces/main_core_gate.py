def classify_main_command(message, model_state=None):
    text = (message or "").strip().lower()

    # Main Surface Gate V1:
    # Only confirmed Gerfex-owned direct commands may enter Gerfex Core.
    # Everything else must go to GMA Native through needs_gma_native=True.
    direct_core_markers = [
        "كروم", "chrome",
        "يوتيوب", "youtube",
        "الإعدادات", "الاعدادات", "اعدادات", "settings",
        "الرئيسية", "home",
        "ارجع", "back",
    ]

    if any(marker in text for marker in direct_core_markers):
        return {
            "path": "gerfex_core",
            "reason": "main_gate_confirmed_gerfex_core_capability"
        }

    return {
        "path": "gerfex_brain",
        "reason": "main_gate_to_gma_native_by_default"
    }
