from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def build_learning_context():
    constitution = _read_text(ROOT / "constitution" / "gma_constitution_v1.md")
    personality = _read_text(ROOT / "personality" / "gma_learning_personality_v1.md")
    developer_role = _read_text(ROOT / "developer_role" / "gma_gerfex_developer_role_v1.md")

    return {
        "constitution": constitution,
        "personality": personality,
        "developer_role": developer_role,
    }


def think_learning_entry(message, learning_state=None):
    context = build_learning_context()

    return {
        "ok": True,
        "surface": "learning",
        "speaker": "GMA",
        "needs_gma_native": True,
        "gma_mode": "learning",
        "gma_prompt": message,
        "learning_context": context,
        "reply": ""
    }
