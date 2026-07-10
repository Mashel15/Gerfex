def reason(prompt, mode="conversation", approved_knowledge=None, learned_skills=None):
    prompt = (prompt or "").strip()
    approved_knowledge = approved_knowledge or []
    learned_skills = learned_skills or []

    if mode == "learning":
        return {
            "ok": True,
            "kind": "learning_discussion",
            "answer": "وصلتني في جلسة التعلم. أستطيع مناقشتها كاقتراح، ولن أعتمدها كمعرفة إلا بموافقة Mashel.",
            "reason": "learning_mode_no_auto_approval"
        }

    return {
        "ok": True,
        "kind": "conversation",
        "answer": "GMA Native هو المسار المعتمد للردود المباشرة. هذا المسار الاحتياطي في Python غير مخصص للمحادثة العادية.",
        "reason": "native_gma_direct_required"
    }
