import time

def _items(data):
    return data.get("items", []) if isinstance(data, dict) else []

def _save_approved_direct(learning_load, APPROVED, lesson):
    import json
    data = learning_load(APPROVED)
    data.setdefault("items", [])

    item = {
        "id": int(time.time() * 1000),
        "lesson": lesson,
        "source": "forced_approval",
        "status": "approved",
        "confidence": 1.0,
        "created_at": time.time(),
        "approved_at": time.time(),
    }

    data["items"].insert(0, item)

    try:
        APPROVED.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        return None

    return item


def _save_pending_direct(learning_load, PENDING, lesson):
    data = learning_load(PENDING)
    data.setdefault("items", [])

    item = {
        "id": int(time.time() * 1000),
        "lesson": lesson,
        "source": "conversation_natural",
        "status": "pending",
        "confidence": 0.80,
        "created_at": time.time(),
    }

    data["items"].insert(0, item)

    try:
        PENDING.write_text(
            __import__("json").dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        return None

    return item

def _latest_pending_id(learning_load, PENDING):
    data = learning_load(PENDING)
    items = _items(data)
    if not items:
        return None
    return items[0].get("id")

def handle_conversational_learning(
    prompt,
    text,
    learning_load=None,
    add_pending_lesson=None,
    approve_lesson=None,
    reject_lesson=None,
    PENDING=None,
    APPROVED=None,
    model_state=None,
):
    if not learning_load:
        return None

    model_state = model_state or {}
    is_learning_session = bool(model_state.get("learning_session"))

    if is_learning_session and "[learning_session]" in (prompt or "").lower() and "اعتمد" in (prompt or "") and APPROVED:
        lesson = prompt.strip()
        lesson = lesson.replace("اعتمد هذه الفكرة", "")
        lesson = lesson.replace("اعتمد هذا", "")
        lesson = lesson.replace("اعتمدها", "")
        lesson = lesson.replace("اعتمد", "")
        lesson = lesson.strip(" .،:؛\n\t")

        if lesson:
            saved = _save_approved_direct(learning_load, APPROVED, lesson)
            if saved:
                return f"تم اعتماد الفكرة مباشرة برقم {saved.get('id')}."
            return "فهمت أمر الاعتماد، لكن لم أستطع حفظ الفكرة."
        return "سمعت أمر الاعتماد، لكن لم أجد فكرة واضحة لاعتمادها."

    approval_words = [
        "موافق", "نعم", "ايه", "تمام", "اعتمدها", "اعتمد هذا",
        "احفظها", "خلها قاعدة", "اعمل بها", "هذه صحيحة",
        "اضفها للمعرفة", "أضفها للمعرفة"
    ]

    reject_words = [
        "ارفضها", "لا تعتمد", "هذا خطأ", "غير صحيح",
        "احذف الدرس", "لا تحفظها"
    ]

    proposal_markers = [
        "عندي قاعدة جديدة", "تعلم من هذا", "احفظ كدرس",
        "خلينا نحفظ", "ملاحظة مهمة", "اعتبرها قاعدة",
        "من الآن", "تذكر أن"
    ]

    correction_markers = [
        "صحح", "تصحيح", "عدّل", "عدل", "المعلومة الصحيحة",
        "الفكرة الصحيحة"
    ]

    if any(w in text for w in proposal_markers + correction_markers):
        lesson = prompt.strip()
        if ":" in lesson:
            lesson = lesson.split(":", 1)[1].strip()

        saved = _save_pending_direct(learning_load, PENDING, lesson)

        if saved:
            return (
                f"فهمت أنها معرفة أو قاعدة جديدة. "
                f"أضفتها إلى دروس الانتظار برقم {saved.get('id')} "
                f"حتى توافق عليها صراحة."
            )

        return "فهمت القاعدة، لكن لم أستطع حفظها في دروس الانتظار."

    if any(w in text for w in approval_words):
        if approve_lesson and PENDING:
            lesson_id = _latest_pending_id(learning_load, PENDING)
            if lesson_id:
                approve_lesson(str(lesson_id))
                return f"تم اعتماد آخر درس مقترح: {lesson_id}"
        return "لا يوجد درس بانتظار الاعتماد."

    if any(w in text for w in reject_words):
        if reject_lesson and PENDING:
            lesson_id = _latest_pending_id(learning_load, PENDING)
            if lesson_id:
                reject_lesson(str(lesson_id))
                return f"تم رفض آخر درس مقترح: {lesson_id}"
        return "لا يوجد درس بانتظار الرفض."

    return None
