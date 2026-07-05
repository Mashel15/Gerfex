# Gerfex Main Surface Gate V1

## الهدف
تثبيت بوابة الشاشة الرئيسية قبل بناء أوامر وسلوكيات جديدة.

## القاعدة الرسمية
الشاشة الرئيسية تخص Gerfex.

داخل الشاشة الرئيسية:
- إذا كان الطلب أمرًا مباشرًا ومعروفًا عند Gerfex، يذهب إلى Gerfex Core.
- إذا كان الطلب سؤالًا عامًا أو أمرًا غير معروف أو يحتاج عقل داخلي، يذهب إلى GMA Native.
- لا يسمح للمسار القديم داخل brain_manager أو gma_provider بقيادة محادثات GMA الجديدة.

## المسار الرسمي

Main UI
→ GerfexPlugin.thinkMain
→ gerfex_entry.think_main
→ surfaces/main_surface.py
→ surfaces/main_core_gate.py

ثم:

1. أوامر Gerfex المباشرة:
   → core/gerfex_core.py
   → execution_manager.py
   → GerfexPlugin native action

2. غير ذلك:
   → needs_gma_native=True
   → GerfexPlugin.fillGmaNativeIfNeeded
   → GmaLlamaBridge
   → JNI / llama.cpp / GGUF

## ملاحظات
قائمة أوامر Gerfex المباشرة الحالية مؤقتة وقابلة للاستبدال لاحقًا.
المهم الآن هو أن تكون البوابة نظيفة ولا تسمح بتداخل القديم مع GMA الجديد.
