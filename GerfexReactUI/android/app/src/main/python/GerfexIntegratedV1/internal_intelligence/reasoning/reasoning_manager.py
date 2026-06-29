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
        "answer": "GMA متصل الآن بمسار GGUF Runtime، لكن llama.cpp native binding لم يتم تركيبه بعد؛ لذلك يعمل fallback مؤقت عبر Reasoning Manager.",
        "reason": "conversation_reasoning_manager_active"
    }
