from pathlib import Path

from GerfexIntegratedV1.internal_intelligence.gerfex_entry_gate.gate import enter_from_main_gma


ROOT = Path(__file__).resolve().parent


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def build_gma_main_context():
    return {
        "constitution": _read_text(ROOT / "constitution_v1.md"),
        "identity": _read_text(ROOT / "identity_v1.md"),
        "objectives": _read_text(ROOT / "objectives_v1.md"),
        "behavior": _read_text(ROOT / "behavior_v1.md"),
    }


def build_gma_main_prompt(message, context):
    return f"""[GMA MAIN MODE]

أنت GMA، الذكاء الداخلي الحالي داخل Gerfex.
أنت هنا تعمل من خلف Gerfex داخل الشاشة الرئيسية، ولست صفحة تعلم مستقلة.

## دستور GMA في المسار الرئيسي
{context.get("constitution", "")}

## هوية GMA في المسار الرئيسي
{context.get("identity", "")}

## أهداف GMA في المسار الرئيسي
{context.get("objectives", "")}

## سلوك GMA في المسار الرئيسي
{context.get("behavior", "")}

## رسالة المستخدم إلى Gerfex
{message}

## قواعد الرد المطلوبة
- أنت تعمل من خلف Gerfex.
- لا تعرّف نفسك للمستخدم باسم GMA في الشاشة الرئيسية.
- الرد النهائي يجب أن يكون مناسبًا ليظهر باسم Gerfex.
- اختصر قدر الإمكان.
- كن واضحًا ومباشرًا.
- لا تستخدم رسائل تقنية أو داخلية.
- إذا كان الطلب خارج صلاحيات التنفيذ أو ليس أمرًا مباشرًا، فقدم ردًا مناسبًا باسم Gerfex.
"""


def think_gma_main_entry(message, model_state=None, route_context=None):
    context = build_gma_main_context()
    gate_result = enter_from_main_gma(message, context={
        "gma_context": context,
        "model_state": model_state or {},
        "route_context": route_context or {},
    })
    prompt = build_gma_main_prompt(message, context)

    return {
        "ok": True,
        "surface": "main",
        "speaker": "Gerfex",
        "path": "gerfex_brain",
        "needs_gma_native": True,
        "gma_mode": "main",
        "gma_prompt": prompt,
        "gma_main_context": context,
        "gerfex_entry_gate": gate_result,
        "reply": ""
    }
