# Gerfex Intelligence Gateway Closed — V1

## الحالة
تم اعتماد `internal_intelligence/gerfex_entry_gate/` كحدّ معماري وحيد بين Gerfex والنماذج.

## القاعدة المعمارية
لا يحق لأي جزء من Gerfex أو أي نموذج ذكاء داخلي/خارجي أن يتجاوز هذا الباب.

المسارات المعتمدة فقط:

### دخول النماذج إلى Gerfex
1. `learning_to_gerfex`
   - من صفحة التعلم إلى Gerfex
   - خاص بنقاشات GMA التعليمية والاقتراحات والاعتماد/الرفض

2. `main_gma_to_gerfex`
   - من GMA الرئيسي إلى Gerfex
   - خاص بمسار GMA الداخلي القادم من الشاشة الرئيسية

### خروج Gerfex إلى النماذج
3. `gerfex_to_internal_model`
   - من Gerfex إلى نموذج داخلي مثل GMA

4. `gerfex_to_external_model`
   - من Gerfex إلى نموذج خارجي عند الحاجة

---

## ما تم إغلاقه في هذا checkpoint

### 1) إغلاق مسار `gerfex_entry.think()` القديم
- تم تحويله إلى:
  - `think() -> think_main() -> main_surface`

### 2) إغلاق `GerfexPlugin.gmaNativeChat()`
- لم يعد بابًا جانبيًا مباشرًا
- أصبح يمر عبر المسار الرئيسي المعتمد

### 3) إغلاق استدعاءات `brain_manager` القديمة إلى GMA/provider
- تم تعطيل الردود القديمة المباشرة
- لم يعد `brain_manager` يستخدم provider loader كمسار ذكاء معتمد

### 4) تعطيل طبقة provider/runtime القديمة
تم عزل أو تعطيل:
- `internal_intelligence/provider/gma_provider.py`
- `internal_intelligence/runtime/gguf_runtime.py`
- `internal_intelligence/runtime/llama_server_runtime.py`
- `internal_intelligence/runtime/provider_registry.json`
- `internal_intelligence/runtime/state.json`

وتم تعطيل:
- `internal_intelligence/provider/provider_loader.py`

### 5) تعطيل `external_models/model_gateway.py` كمسار مباشر
- لم يعد مسموحًا لأي جزء من Gerfex استدعاء external models مباشرة من خلاله
- تم إبقاؤه كملف disabled/compatibility فقط

### 6) تعديل `testExternalModel` في `GerfexPlugin.java`
- لم يعد يستدعي `external_models.model_gateway`
- أصبح يمر عبر:
  - `internal_intelligence.gerfex_entry_gate.gate`

---

## البنية الحالية المعتمدة

### صفحة التعلم
`gerfex_entry.think_learning`
→ `surfaces.learning_surface`
→ `internal_intelligence.learning.gma_learning_entry`
→ `internal_intelligence.gerfex_entry_gate.enter_from_learning`

### الشاشة الرئيسية / GMA الداخلي
`gerfex_entry.think_main`
→ `surfaces.main_surface`
→ `internal_intelligence.gma.main.gma_main_entry`
→ `internal_intelligence.gerfex_entry_gate.enter_from_main_gma`

### خروج Gerfex إلى النماذج
أي طلب من Gerfex إلى نموذج يجب أن يمر عبر:
- `gerfex_to_internal_model(...)`
- `gerfex_to_external_model(...)`

---

## سياسة التطوير من الآن فصاعدًا
1. أي ربط جديد مع نموذج داخلي أو خارجي يجب أن يمر عبر `gerfex_entry_gate`.
2. أي ملف قديم يحاول الوصول المباشر إلى provider/runtime/model gateway يعتبر Legacy وغير معتمد.
3. لا يجوز إعادة إحياء المسارات القديمة إلا بقرار معماري صريح من Mashel.
4. إذا ظهر استدعاء جديد مباشر إلى نموذج خارج البوابة، يعتبر خلل معماري يجب إصلاحه قبل البناء النهائي.

---

## الخلاصة
تم إغلاق المسارات القديمة الأساسية، وأصبح `gerfex_entry_gate` هو الحدّ المعماري الرسمي الوحيد بين Gerfex وطبقة النماذج.
