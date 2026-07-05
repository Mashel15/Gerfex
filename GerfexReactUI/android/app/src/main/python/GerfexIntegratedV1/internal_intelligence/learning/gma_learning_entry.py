from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
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


def build_learning_prompt(message, context):
    return f"""[GMA LEARNING MODE]

أنت الآن داخل صفحة التعلم الخاصة بمشروع Gerfex.
هذه الصفحة ليست صفحة تنفيذ أوامر Android وليست الواجهة الرئيسية لـ Gerfex.
أنت هنا باسمك الحقيقي GMA، ودورك هو النقاش والتحليل واقتراح التطوير لصالح Gerfex فقط.

## دستور GMA
{context.get("constitution", "")}

## شخصية GMA في صفحة التعلم
{context.get("personality", "")}

## دور GMA كمطور لـ Gerfex
{context.get("developer_role", "")}

## رسالة Mashel
{message}

## طريقة الرد المطلوبة
- رد بصفتك GMA.
- ركز على التحليل أو الاقتراح أو الإجابة التعليمية.
- لا تتصرف كمنفذ أوامر Android.
- لا تدّعي اعتماد أي قاعدة جديدة من نفسك.
- إذا كان الكلام اقتراحًا أو رأيًا تطويريًا فوضحه بصراحة.
"""


def think_learning_entry(message, learning_state=None):
    context = build_learning_context()
    prompt = build_learning_prompt(message, context)

    return {
        "ok": True,
        "surface": "learning",
        "speaker": "GMA",
        "needs_gma_native": True,
        "gma_mode": "learning",
        "gma_prompt": prompt,
        "learning_context": context,
        "reply": ""
    }
