from pathlib import Path

class GGUFRuntime:
    def __init__(self, model_path=None, model_asset=None):
        self.model_path = model_path
        self.model_asset = model_asset
        self.loaded = False
        self.engine = "llama.cpp"
        self.error = None

    def status(self):
        return {
            "ok": True,
            "engine": self.engine,
            "loaded": self.loaded,
            "model_path": self.model_path,
            "model_asset": self.model_asset,
            "note": "GGUF model is served through Android Native GmaLlamaBridge/JNI, not this Python fallback adapter."
        }

    def generate(self, prompt, **kwargs):
        return {
            "ok": False,
            "reply": "GMA Native يعمل عبر Android JNI. هذا المسار Python fallback غير مخصص للمحادثة المباشرة.",
            "reason": "use_android_gma_native_bridge",
            "engine": self.engine,
            "model_path": self.model_path,
            "model_asset": self.model_asset
        }
