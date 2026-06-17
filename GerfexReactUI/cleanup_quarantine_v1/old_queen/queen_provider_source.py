import json
import time
from pathlib import Path

try:
    from queen_intelligence import queen_answer
except Exception:
    queen_answer = None

BASE = Path(__file__).parent
LEARNING = BASE.parent / "learning"
APPROVED = LEARNING / "approved_knowledge.json"
IDENTITY = BASE / "identity.json"

def load_json(path, default):
    try:
        if Path(path).exists():
            return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def clean_lesson(text):
    t = (text or "").strip()
    for w in ["اعتمد", "اعتمد الجلسة", "اعتماد"]:
        t = t.replace(w, "")
    return t.strip(" .،:\n\t")

def search_knowledge(question, items):
    q = (question or "").strip().lower()
    for item in items:
        lesson = (item.get("lesson") or "").strip()
        low = lesson.lower()
        words = [w for w in q.replace("؟", "").split() if len(w) > 2]
        score = sum(1 for w in words if w in low)
        if score >= 2:
            return lesson
    return None

def queen_think(prompt, selected_model="Queen", model_state=None):
    model_state = model_state or {}
    text = (prompt or "").strip()
    low = text.lower()

    if not model_state.get("learning_session"):
        return {
            "reply": "Queen يعمل فقط داخل صفحة التعلم.",
            "speaker": "Queen",
            "core": "Queen",
            "status": "blocked_outside_learning"
        }

    if low in ["من انت", "من أنت", "عرف نفسك"]:
        return {
            "reply": "أنا Queen، نظام تعلم بسيط. وظيفتي حفظ المعرفة المعتمدة واسترجاعها داخل صفحة التعلم فقط. لا أدير Gerfex ولا أنفذ أوامر.",
            "speaker": "Queen",
            "core": "Queen",
            "status": "ok"
        }

    data = load_json(APPROVED, {"items": []})
    items = data.get("items", [])

    if "اعرض المعرفة" in text or "المعرفة المعتمدة" in text:
        if not items:
            reply = "لا توجد معرفة معتمدة."
        else:
            reply = "المعرفة المعتمدة:\n" + "\n".join(
                [f"- {x.get('id')}: {x.get('lesson')}" for x in items[:20]]
            )
        return {"reply": reply, "speaker": "Queen", "core": "Queen", "status": "ok"}

    if "اعتمد" in text:
        lesson = clean_lesson(text)
        if not lesson:
            reply = "لا توجد معلومة واضحة لاعتمادها."
        else:
            item = {"id": int(time.time() * 1000), "lesson": lesson}
            items.insert(0, item)
            data["items"] = items
            save_json(APPROVED, data)
            reply = f"تم اعتماد المعرفة برقم {item['id']}."
        return {"reply": reply, "speaker": "Queen", "core": "Queen", "status": "ok"}

    # المعرفة المعتمدة أعلى من معرفة Queen الطبيعية
    found = search_knowledge(text, items)
    if found:
        return {"reply": found, "speaker": "Queen", "core": "Queen", "status": "ok", "source": "approved_knowledge"}

    # إذا لا توجد معرفة معتمدة، استخدم ذكاء Queen الطبيعي داخل صفحة التعلم فقط
    if queen_answer:
        reply = queen_answer(prompt)
    else:
        reply = "أنا Queen داخل صفحة التعلم. لا أملك نموذجاً طبيعياً متصلاً حالياً."

    return {
        "reply": reply,
        "speaker": "Queen",
        "core": "Queen",
        "status": "ok",
        "source": "queen_natural_fallback"
    }
