def classify_learning_prompt(text: str) -> dict:
    text = (text or "").strip()

    question_markers = [
        "ما هو", "ماهي", "ما هي", "هل", "كيف", "لماذا",
        "ما الفرق", "اشرح", "وضح", "يعني", "؟", "?"
    ]

    improvement_markers = [
        "اقترح تطوير", "طوّر", "طور", "تحسين", "حسّن",
        "اضف ميزة", "أضف ميزة", "تطوير مجلد", "improvement"
    ]

    lesson_markers = [
        "تذكر أن", "احفظ أن", "تعلم أن", "قاعدة", "درس",
        "لا تعتمد", "يجب أن", "ممنوع", "اسمح"
    ]

    if any(m in text for m in question_markers):
        return {
            "ok": True,
            "kind": "question",
            "answer": "هذا سؤال داخل مسار الذكاء الداخلي. يتم شرحه أو الرد عليه فقط بدون حفظه كدرس أو تطوير.",
            "reason": "detected_as_question_no_learning_saved"
        }

    if any(m in text for m in improvement_markers):
        return {
            "ok": True,
            "kind": "improvement",
            "proposal": text,
            "reason": "detected_as_improvement_proposal"
        }

    if any(m in text for m in lesson_markers):
        return {
            "ok": True,
            "kind": "lesson",
            "proposal": text,
            "reason": "detected_as_lesson_proposal"
        }

    return {
        "ok": True,
        "kind": "question",
        "answer": "لم يتم اكتشاف درس أو تطوير واضح. سأتعامل معها كسؤال/نقاش بدون حفظ.",
        "reason": "default_question_no_learning_saved"
    }


def think_about_learning(text: str, approved_knowledge=None, learned_skills=None, **kwargs) -> dict:
    return classify_learning_prompt(text)

def _text_of(item):
    if isinstance(item, dict):
        for key in ("text", "lesson", "content", "knowledge", "rule", "proposal"):
            value = item.get(key)
            if value:
                return str(value)
        return str(item)
    return str(item)


def _find_relevant_items(text, items, limit=3):
    text = (text or "").strip().lower()
    words = [w for w in text.replace("؟", " ").replace("?", " ").split() if len(w) > 2]
    scored = []
    for item in items or []:
        body = _text_of(item)
        b = body.lower()
        score = sum(1 for w in words if w in b)
        if score:
            scored.append((score, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [body for _, body in scored[:limit]]


def think_about_conversation(text: str, approved_knowledge=None, learned_skills=None, **kwargs) -> dict:
    text = (text or "").strip()
    approved_knowledge = approved_knowledge or []
    learned_skills = learned_skills or []

    relevant_knowledge = _find_relevant_items(text, approved_knowledge)
    relevant_skills = _find_relevant_items(text, learned_skills)

    if relevant_knowledge or relevant_skills:
        parts = []
        if relevant_knowledge:
            parts.append("من المعرفة المعتمدة: " + " | ".join(relevant_knowledge))
        if relevant_skills:
            parts.append("من المهارات المتعلمة: " + " | ".join(relevant_skills))
        return {
            "ok": True,
            "kind": "conversation",
            "answer": "\n".join(parts),
            "reason": "conversation_answer_from_internal_memory",
            "approved_knowledge_count": len(approved_knowledge),
            "learned_skills_count": len(learned_skills)
        }

    return {
        "ok": True,
        "kind": "conversation",
        "answer": (
            "لا أملك معرفة معتمدة كافية داخل GMA للإجابة بثقة على هذا السؤال بعد. "
            "أستطيع مناقشته معك أو تحويله إلى بحث/تعلم إذا اعتمدته."
        ),
        "reason": "conversation_no_relevant_internal_knowledge",
        "approved_knowledge_count": len(approved_knowledge),
        "learned_skills_count": len(learned_skills)
    }

