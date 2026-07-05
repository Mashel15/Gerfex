# Gerfex Intelligence Gateway Policy V1

## القاعدة

أي تواصل بين Gerfex ونماذج الذكاء يجب أن يمر من هذا المجلد فقط.

## ممنوع

- ممنوع أن يستدعي Gerfex نموذجًا داخليًا مباشرة من core أو brain أو surfaces.
- ممنوع أن يستدعي Gerfex نموذجًا خارجيًا مباشرة من external_models بدون المرور من البوابة.
- ممنوع أن يدخل GMA إلى Gerfex من مسار جانبي.
- ممنوع أن تتواصل صفحة التعلم مع Gerfex إلا عبر learning_to_gerfex.

## مسموح

- GMA Learning → Gateway → Gerfex
- GMA Main → Gateway → Gerfex
- Gerfex → Gateway → Internal Model
- Gerfex → Gateway → External Model

## الحالة

هذه سياسة معمارية.
أي ملف قديم يخالفها يعتبر legacy إلى أن يتم عزله أو تحويله.
