from pathlib import Path

from GerfexIntegratedV1.internal_intelligence.gerfex_entry_gate.gate import enter_from_main_gma


ROOT = Path(__file__).resolve().parent
SECTIONS = ROOT / "sections"


SECTION_ORDER = [
    "01_identity.md",
    "02_purpose.md",
    "03_reasoning.md",
    "04_behavior.md",
    "05_learning.md",
    "06_authority.md",
    "07_boundaries.md",
    "08_gerfex_interface.md",
]


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def build_gma_main_context():
    context = {}
    for name in SECTION_ORDER:
        key = name.replace(".md", "")
        context[key] = _read_text(SECTIONS / name)
    return context


def build_gma_main_prompt(message, context):
    sections_text = "\n\n".join(context.get(name.replace(".md", ""), "") for name in SECTION_ORDER)

    return f"""[GMA MAIN MODE]

أنت GMA داخل المسار الرئيسي لـ Gerfex.
اتبع تعليماتك الخاصة كنموذج ذكاء داخلي من الأقسام التالية:

{sections_text}

## رسالة المستخدم إلى Gerfex
{message}

## أمر الرد
- أجب من خلف Gerfex.
- لا تذكر أنك GMA.
- اجعل الرد مناسبًا ليظهر باسم Gerfex.
- اختصر قدر الإمكان.
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
