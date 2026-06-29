GMA Q2 model is embedded in APK:
assets/GerfexModels/google_gemma-3-4b-it-Q2_K.gguf

Current state:
- GMA provider connected.
- GGUF runtime adapter created.
- Native llama.cpp binding is still pending.

Termux result:
- Android NDK installed as linux-x86_64.
- Its clang/cmake are not executable on Android Termux aarch64.
- Building llama.android AAR locally on phone is not clean.

Approved next step:
Build llama.android AAR on GitHub Actions or PC, then integrate the produced AAR/.so into Gerfex APK.
