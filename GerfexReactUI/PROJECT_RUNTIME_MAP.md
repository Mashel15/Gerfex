# Gerfex Runtime Map

## Current Baseline

Active project path:

`~/GerfexGitHub/Gerfex/GerfexReactUI`

Current confirmed baseline commit:

`805a412 Force native library extraction for GMA runtime`

GMA Native has already worked inside Gerfex. The previous `loaded=0` native-loading issue is not the default starting point anymore.

Do not restart native-loading diagnosis unless new logcat evidence shows a new native error.

## Official Architecture Split

Gerfex currently has two separate official responsibilities:

1. GMA Native
   - Used for general chat, factual questions, knowledge answers, and normal conversation.

2. Gerfex Python Core
   - Used for Gerfex commands, Android/device execution, memory, learning, planning, and orchestration.

These two paths must not be mixed.

## Official GMA Native Runtime Path

The official GMA runtime path is:

`src/App.jsx`
-> `GerfexNative.gmaNativeChat()`
-> `android/app/src/main/java/com/mashel15/gerfex/GerfexPlugin.java`
-> `gmaNativeChat()`
-> `ensureGmaModelFile()`
-> `android/app/src/main/java/com/mashel15/gerfex/GmaLlamaBridge.kt`
-> `android/app/src/main/cpp/gerfex_llama_jni.cpp`
-> llama / ggml native libraries
-> GGUF model

This is the real GMA path.

## Official Gerfex Python Core Runtime Path

The official Python Core path is:

`src/App.jsx`
-> Gerfex native bridge / `think`
-> `android/app/src/main/java/com/mashel15/gerfex/GerfexPlugin.java`
-> `think()`
-> embedded Python / GerfexIntegratedV1
-> brain / execution / memory / learning / command routing

This path is for Gerfex behavior, not for diagnosing GMA Native.

## Legacy / Misleading GMA-Named Python Paths

The following files are not the real GMA Native runtime:

- `GerfexIntegratedV1/internal_intelligence/provider/gma_provider.py`
- `GerfexIntegratedV1/internal_intelligence/runtime/gguf_runtime.py`

They must not be treated as the official GMA engine.

At this stage, do not rename or move them. Only add clear warning comments if needed, because renaming or moving may break old Python imports.

## Routing Policy V1

General chat goes to GMA Native:

- greetings
- factual questions
- explanations
- normal conversation
- knowledge prompts

Gerfex commands go to Python Core:

- open apps
- execute device actions
- search workflows
- memory commands
- learning commands
- planning / orchestration tasks

Mixed execution-heavy tasks stay under Python Core orchestration.

Example:

"افتح كروم وابحث عن أفضل مطاعم الرياض ثم لخص لي أول نتيجتين"

This should be handled by Python Core first because it requires execution and orchestration.

## Files Not To Touch Casually

Do not casually edit these files unless the Routing Audit or logcat proves a need:

- `src/App.jsx`
  - Do not edit routing here before Routing Audit proves it is needed.

- `android/app/src/main/java/com/mashel15/gerfex/GerfexPlugin.java`
  - Contains both `think()` and `gmaNativeChat()` paths.

- `android/app/src/main/java/com/mashel15/gerfex/GmaLlamaBridge.kt`
  - Native library loading bridge.

- `android/app/src/main/cpp/gerfex_llama_jni.cpp`
  - Real GMA generation engine.

- `android/app/src/main/cpp/CMakeLists.txt`
  - Native build configuration.

- `android/app/build.gradle`
  - Contains required native packaging settings.

- `android/app/src/main/AndroidManifest.xml`
  - Contains required `android:extractNativeLibs="true"`.

- `android/app/libs/llama-android-lib-release.aar`
  - May contain required llama / ggml native libraries.
  - Do not delete until a safe tested replacement exists.

## Required Native Baseline Settings

`AndroidManifest.xml` must keep:

`android:extractNativeLibs="true"`

`android/app/build.gradle` must keep:

`packaging { jniLibs { useLegacyPackaging = true } }`

These are part of the working GMA Native baseline.

## Success / Failure Definitions

GMA Native success means:

- the APK sends the prompt through `gmaNativeChat`
- JNI loads successfully
- at least one backend is loaded
- model loads
- a real model reply is returned

GMA Native failure examples:

- `GMA_LLAMA_ERROR`
- `GMA_LLAMA_EMPTY_REPLY`
- `no_backend_loaded`
- `model_load_null`
- `context_null`
- `jniLoaded=false`
- backend count equals zero

Python Core failure examples:

- `think()` failure
- embedded Python failure
- routing failure
- execution_manager failure
- brain_manager / memory / learning failure

## Current Work Order

1. Documentation.
2. Routing Audit.
3. Routing Policy confirmation.
4. Conditional implementation.
5. One intentional build.
6. Gradual cleanup.

Important rule:

Do not edit `App.jsx` before Routing Audit proves the routing decision is ambiguous, scattered, or has unsafe fallback.

Important rule:

For `gma_provider.py` and `gguf_runtime.py`, use warning comments only at this stage. Do not rename or move them yet.
