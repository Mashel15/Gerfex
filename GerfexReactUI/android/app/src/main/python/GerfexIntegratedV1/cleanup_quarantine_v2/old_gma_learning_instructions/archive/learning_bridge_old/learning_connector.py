from pathlib import Path
import json

BASE = Path(__file__).resolve().parent.parent / "queen_learning"

PENDING = BASE / "pending_lessons.json"
APPROVED = BASE / "approved_knowledge.json"
SKILLS = BASE / "learned_skills.json"
RULES = BASE / "learned_rules.json"


def _load(path):
    if not path.exists():
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def pending_lessons():
    return _load(PENDING)


def approved_knowledge():
    return _load(APPROVED)


def learned_skills():
    return _load(SKILLS)


def learned_rules():
    return _load(RULES)
