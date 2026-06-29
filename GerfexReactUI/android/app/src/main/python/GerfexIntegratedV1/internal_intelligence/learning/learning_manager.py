from pathlib import Path
import json
import time

BASE = Path(__file__).resolve().parent

PENDING_LESSONS = BASE / "pending_lessons.json"
APPROVED_KNOWLEDGE = BASE / "approved_knowledge.json"
LEARNED_SKILLS = BASE / "learned_skills.json"
LEARNED_RULES = BASE / "learned_rules.json"
PENDING_IMPROVEMENTS = BASE / "pending_improvements.json"
APPROVED_IMPROVEMENTS = BASE / "approved_improvements.json"


def _load(path):
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _item(text, kind):
    return {
        "id": int(time.time() * 1000),
        "kind": kind,
        "text": text,
        "status": "pending",
        "created_at": time.time()
    }


def pending_lessons():
    return _load(PENDING_LESSONS)


def approved_knowledge():
    return _load(APPROVED_KNOWLEDGE)


def learned_skills():
    return _load(LEARNED_SKILLS)


def learned_rules():
    return _load(LEARNED_RULES)


def pending_improvements():
    return _load(PENDING_IMPROVEMENTS)


def approved_improvements():
    return _load(APPROVED_IMPROVEMENTS)


def propose_lesson(text):
    data = pending_lessons()
    item = _item(text, "lesson")
    data.insert(0, item)
    _save(PENDING_LESSONS, data)
    return item


def approve_latest_lesson():
    pending = pending_lessons()
    if not pending:
        return {"ok": False, "reason": "no_pending_lessons"}

    item = pending.pop(0)
    item["status"] = "approved"
    item["approved_at"] = time.time()

    approved = approved_knowledge()
    approved.insert(0, item)

    _save(PENDING_LESSONS, pending)
    _save(APPROVED_KNOWLEDGE, approved)

    return {"ok": True, "approved": item}


def reject_latest_lesson():
    pending = pending_lessons()
    if not pending:
        return {"ok": False, "reason": "no_pending_lessons"}

    item = pending.pop(0)
    item["status"] = "rejected"
    item["rejected_at"] = time.time()

    _save(PENDING_LESSONS, pending)
    return {"ok": True, "rejected": item}


def propose_improvement(text):
    data = pending_improvements()
    item = _item(text, "improvement")
    data.insert(0, item)
    _save(PENDING_IMPROVEMENTS, data)
    return item


def approve_latest_improvement():
    pending = pending_improvements()
    if not pending:
        return {"ok": False, "reason": "no_pending_improvements"}

    item = pending.pop(0)
    item["status"] = "approved"
    item["approved_at"] = time.time()

    approved = approved_improvements()
    approved.insert(0, item)

    _save(PENDING_IMPROVEMENTS, pending)
    _save(APPROVED_IMPROVEMENTS, approved)

    return {"ok": True, "approved": item}
