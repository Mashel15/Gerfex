from pathlib import Path
import json
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "learning" / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)

PENDING_FILE = RUNTIME / "gma_learning_pending.json"
APPROVED_FILE = RUNTIME / "gma_learning_approved.json"
REJECTED_FILE = RUNTIME / "gma_learning_rejected.json"


APPROVE_WORDS = {"اعتمد", "اعتمد الجلسة"}
REJECT_WORDS = {"لا تعتمد", "لا تعتمد الجلسة"}


def _now():
    return datetime.utcnow().isoformat() + "Z"


def _load(path):
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(path, data):
    path.write_text(json.dumps(data[-300:], ensure_ascii=False, indent=2), encoding="utf-8")


def classify_learning_command(message):
    text = (message or "").strip()
    if text in APPROVE_WORDS:
        return "approve"
    if text in REJECT_WORDS:
        return "reject"
    return "discussion"


def add_pending(message, context=None):
    data = _load(PENDING_FILE)
    item = {
        "time": _now(),
        "message": message,
        "context": context or {},
        "status": "pending"
    }
    data.append(item)
    _save(PENDING_FILE, data)
    return item


def approve_latest():
    pending = _load(PENDING_FILE)
    if not pending:
        return {"ok": False, "reply": "لا توجد مادة تعلم معلقة للاعتماد."}

    item = pending.pop()
    item["status"] = "approved"
    item["approved_time"] = _now()

    approved = _load(APPROVED_FILE)
    approved.append(item)

    _save(PENDING_FILE, pending)
    _save(APPROVED_FILE, approved)

    return {"ok": True, "reply": "تم اعتماد آخر مادة تعلم معلقة."}


def reject_latest():
    pending = _load(PENDING_FILE)
    if not pending:
        return {"ok": False, "reply": "لا توجد مادة تعلم معلقة للرفض."}

    item = pending.pop()
    item["status"] = "rejected"
    item["rejected_time"] = _now()

    rejected = _load(REJECTED_FILE)
    rejected.append(item)

    _save(PENDING_FILE, pending)
    _save(REJECTED_FILE, rejected)

    return {"ok": True, "reply": "تم رفض آخر مادة تعلم معلقة."}
