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
            "note": "GGUF runtime adapter exists. Native llama.cpp binding is not connected yet."
        }

    def generate(self, prompt, **kwargs):
        return {
            "ok": False,
            "reply": "GGUF Runtime موجود، لكن محرك llama.cpp الأصلي لم يتم ربطه بعد.",
            "reason": "native_llama_cpp_not_connected_yet",
            "engine": self.engine,
            "model_path": self.model_path,
            "model_asset": self.model_asset
        }
