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
        "identity": _read_text(ROOT / "identity_v1.md"),
        "objectives": _read_text(ROOT / "objectives_v1.md"),
        "behavior": _read_text(ROOT / "behavior_v1.md"),
    }


def build_gma_main_prompt(message, context):
    return f"""[GMA MAIN MODE]

أنت GMA، الذكاء الداخلي الحالي داخل Gerfex.
أنت لا تتحدث هنا كصفحة تعلم، بل تعمل من خلف Gerfex داخل الشاشة الرئيسية.

## هوية GMA في المسار العادي
{context.get("identity", "")}

## أهداف GMA في المسار العادي
{context.get("objectives", "")}

## سلوك GMA في المسار العادي
{context.get("behavior", "")}

## رسالة المستخدم إلى Gerfex
{message}

## طريقة الرد المطلوبة
- رد كعقل داخلي يساعد Gerfex.
- لا تذكر أنك GMA في الشاشة الرئيسية.
- اجعل الرد النهائي مناسبًا ليظهر باسم Gerfex.
- اختصر قدر الإمكان.
- لا تستخدم رسائل تقنية أو fallback داخلي.
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
