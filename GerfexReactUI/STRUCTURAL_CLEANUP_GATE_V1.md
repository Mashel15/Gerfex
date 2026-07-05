# Gerfex Structural Cleanup Gate V1

## هدف المرحلة

تثبيت البنية الرسمية الحالية قبل بدء المرحلة الثانية الخاصة ببناء الأوامر والتعليمات والسلوكيات الجديدة.

## الحكم الحالي

المشروع وصل إلى بنية انتقالية ناجحة، لكنه ليس نظيفًا بالكامل ما دام المسار القديم يستطيع قيادة ردود GMA عبر:

- core/gerfex_core.py
- brain/brain_manager.py
- internal_intelligence/provider/gma_provider.py
- internal_intelligence/runtime/gguf_runtime.py

## المسار الرسمي الجديد

### الشاشة الرئيسية

UI Main Chat
→ GerfexPlugin.thinkMain
→ gerfex_entry.think_main
→ surfaces/main_surface.py

ثم:

1. إذا كان الأمر مباشرًا ومعتمدًا داخل Gerfex:
   → core/gerfex_core.py
   → core/execution_manager.py
   → GerfexPlugin native action

2. إذا كان السؤال/الأمر غير معروف أو يحتاج عقل داخلي:
   → needs_gma_native=True
   → GerfexPlugin.fillGmaNativeIfNeeded
   → GmaLlamaBridge
   → JNI / llama.cpp / GGUF

### صفحة التعلم

UI Learning
→ GerfexPlugin.thinkLearning
→ gerfex_entry.think_learning
→ surfaces/learning_surface.py
→ needs_gma_native=True
→ GerfexPlugin.fillGmaNativeIfNeeded
→ GMA Native

## قاعدة منع التداخل

لا يجوز للمسار القديم داخل brain_manager أو gma_provider أن يقود محادثات GMA الجديدة.

brain_manager يبقى فقط كجزء legacy/compatibility داخل Gerfex Core إلى أن يتم استبداله تدريجيًا.

## ما لا نفعله الآن

- لا نحذف الملفات القديمة.
- لا نعيد كتابة التعليمات.
- لا نبني قوائم أوامر نهائية.
- لا نحسن أسلوب الرد.
- لا نحذف fallback القديم الآن.

## المطلوب قبل المرحلة الثانية

- عزل GMA الجديد عن brain_manager القديم.
- جعل surfaces هي بوابة القرار الرسمية.
- إدخال run_goal فقط للأوامر المباشرة المؤكدة.
- إرسال كل غير معروف إلى GMA Native.
