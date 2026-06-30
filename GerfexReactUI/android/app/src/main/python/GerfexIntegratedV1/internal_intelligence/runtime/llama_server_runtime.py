import json
import urllib.request

class LlamaServerRuntime:
    def __init__(self, url="http://127.0.0.1:8080/completion"):
        self.url = url
        self.engine = "llama.cpp-server"

    def generate(self, prompt, predict_length=64):
        payload = {
            "prompt": "أجب بالعربية فقط.\n" + str(prompt),
            "n_predict": int(predict_length),
            "temperature": 0.4,
            "stream": False
        }

        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=180) as r:
                obj = json.loads(r.read().decode("utf-8"))

            return {
                "ok": True,
                "engine": self.engine,
                "reply": obj.get("content", "").strip(),
            }

        except Exception as e:
            return {
                "ok": False,
                "reason": "llama_server_error",
                "error": str(e),
            }
