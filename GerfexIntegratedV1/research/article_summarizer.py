import json
from pathlib import Path

SRC = Path("research/last_article_read.json")
OUT = Path("research/last_article_summary.txt")

BAD = [
    "إعلان",
    "انقر هنا",
    "رابط إلى",
    "Instagram",
    "jpg",
    "alhadath",
    "تم التحقق",
    "متابعين",
    "منشورًا",
    "🔴",
    "EOF",
    "python -m",
    "Path(",
    "summary",

    # site chrome / ads / finance widgets
    "Investing.com - البوابة الإقتصادية الرائدة",
    "الرسوم البيانية",
    "منصات تداول",
    "تقويم",
    "🚀",
    "احصل على تحديثات",
    "مدرج ضمن",
    "رأيت الصفقة",
    "قراءة الرسوم",
    "سجِّل الدخول",
    "سجّل الدخول",
    "©",
    "جاري تحميل المقال التالي",
    "كل الحقوق محفوظة",
    "البطاقة السفلية",
    "google.com",
    "user?screen_name",
    "samsung-electronics-co-ltd",
]


def is_bad_text(p):
    p = " ".join(str(p).split())

    if len(p) < 45:
        return True

    for b in BAD:
        if b in p:
            return True

    return False


def summarize():
    if not SRC.exists():
        return {"ok": False, "summary": "لا يوجد مقال مقروء."}

    data = json.loads(SRC.read_text(encoding="utf-8"))

    if not data.get("ok"):
        msg = f"فشل التلخيص: القراءة غير صالحة. السبب: {data.get('reason', 'unknown')}"
        OUT.write_text(msg, encoding="utf-8")
        return {"ok": False, "summary": msg}

    title = data.get("title", "").strip()
    paragraphs = data.get("paragraphs", [])

    useful = []

    for p in paragraphs:
        p = " ".join(str(p).split())

        if is_bad_text(p):
            continue

        ad_noise = [
            "أسهم مقومة", "اعرض الأسهم", "InvestingPro",
            "رأيت الصفقة", "قراءة الرسوم", "حاسبة القيمة العادلة",
            "ProPicks", "005930", "الرسوم البيانية",
            "منصات تداول", "تقويم انتهاء", "البوابة الإقتصادية",
            "مدرج ضمن", "سجِّل الدخول", "جاري تحميل",
            "كل الحقوق محفوظة", "user?screen_name"
        ]

        if any(x in p for x in ad_noise):
            continue

        useful.append(p)

    if not title or len(useful) < 3:
        msg = "فشل التلخيص: النص المستخرج غير كافٍ أو يحتوي على عناصر جانبية أكثر من متن المقال."
        OUT.write_text(msg, encoding="utf-8")
        return {"ok": False, "summary": msg}

    main = useful[:6]

    summary = "ملخص المقال:\n\n"
    summary += f"العنوان:\n{title}\n\n"
    summary += "الفكرة الرئيسية:\n"
    summary += main[0] + "\n\n"
    summary += "أهم النقاط:\n"

    for i, p in enumerate(main[1:5], 1):
        summary += f"{i}. {p}\n"

    summary += "\nخلاصة Gerfex:\n"
    summary += "تم فتح المقال وقراءته من الشاشة الحالية، وهذا الملخص مبني على النص المستخرج فعليًا من المقال.\n"

    OUT.write_text(summary, encoding="utf-8")
    return {"ok": True, "summary": summary}


if __name__ == "__main__":
    print(summarize()["summary"])
