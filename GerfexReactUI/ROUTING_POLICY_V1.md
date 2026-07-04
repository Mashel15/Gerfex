# Gerfex Routing Policy V1

## Purpose

This file defines the approved routing policy between:

- GMA Native
- Gerfex Python Core

The goal is to prevent routing confusion and stop sending all main chat messages to GMA by default.

## Core rule

Gerfex must separate:

1. GMA Native
   - for general chat, knowledge, explanation, and conversational prompts

2. Gerfex Python Core
   - for commands, execution, orchestration, memory, and learning governance

## Route 1: GMA Native

Send the prompt to GMA Native when the prompt is primarily conversational or informational.

Examples:
- مرحبا
- كيف حالك
- ماهي عاصمة باكستان
- اشرح لي مفهوم الذكاء الاصطناعي
- ما رأيك في كذا
- عرف لي هذا المصطلح
- لخص لي هذا المفهوم نظريًا بدون تنفيذ

Typical GMA categories:
- greetings
- small talk
- factual questions
- general explanations
- knowledge prompts
- pure conversational replies

## Route 2: Python Core

Send the prompt to Python Core when the prompt is primarily a Gerfex action, command, execution request, planning request, or learning/memory request.

Examples:
- افتح اليوتيوب
- افتح كروم
- ابحث عن أفضل مطاعم الرياض
- افتح الإعدادات
- احفظ هذه المعلومة
- تذكر هذا الشيء
- علّم Gerfex هذا الدرس
- اعتمد الدرس
- لا تعتمد الدرس
- نفذ هذه المهمة
- افحص الشاشة
- اقرأ نتيجة التنفيذ
- افتح التطبيق ثم ابحث ثم ارجع لي النتيجة

Typical Python Core categories:
- Android/device commands
- app launching
- UI execution
- search workflows that require action
- memory operations
- learning approval / governance
- execution planning
- runtime inspection
- mixed orchestration tasks

## Mixed prompts

If the prompt contains both execution and reasoning, route it to Python Core first.

Examples:
- افتح كروم وابحث عن أفضل مطاعم الرياض ثم لخص أول نتيجتين
- افتح يوتيوب وابحث عن فيديو معين ثم أخبرني بما وجدته
- افتح الإعدادات واذكر لي حالة الخيار الفلاني
- نفذ المهمة ثم لخص لي ما حدث

Rule:
If execution is required before an answer can be produced, Python Core owns the request.

## Learning session policy

Current approved direction:

- Learning discussion text may still be generated through the GMA Native conversation path if the current Learning page intentionally uses GMA as the conversational teacher/brain.
- However, lesson approval, rejection, storage, governance, and any real learning-state mutation must remain under Python Core governance.

This means the project must not confuse:
- learning conversation
with
- learning approval/storage execution

## Routing implementation principle

Routing must not depend only on:

- modelState.name === "GMA"
- connected / hold / mute flags

That check only tells whether GMA is available.
It does NOT tell whether the prompt should go to GMA or Python Core.

A lightweight route classifier must exist before deciding between:
- gmaNativeChat
- think

## Current implementation guidance

Before calling `askGerfexNative`, the app should classify the prompt into one of two routes:

- `gma_native`
- `python_core`

Then:

- `gma_native` -> call GMA Native path
- `python_core` -> call Python Core path

## Non-goals of this policy

This policy does not authorize:
- UI redesign
- native JNI redesign
- changing GmaLlamaBridge behavior
- renaming legacy Python GMA files
- deleting AAR/native libs
- changing unrelated Gerfex architecture

It only defines how routing should work.

## Approved next implementation step

After this policy is saved, the next controlled patch should do only the following:

1. Add a small route classifier in `src/App.jsx`
2. Route conversational prompts to GMA Native
3. Route command/execution/memory/learning-governance prompts to Python Core
4. Keep the change as small as possible
5. Avoid unrelated refactoring
6. Avoid build until the patch is fully prepared
