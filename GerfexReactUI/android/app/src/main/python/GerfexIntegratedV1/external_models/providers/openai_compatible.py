import json
import urllib.request

def ask(prompt, provider):
    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "").rstrip("/")
    model = provider.get("model", "")

    if not api_key or not base_url or not model:
        return {
            "ok": False,
            "provider": provider.get("name", "openai_compatible"),
            "reply": "بيانات النموذج الخارجي ناقصة: api_key/base_url/model",
        }

    url = base_url + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "أنت نموذج خارجي مستشار فقط داخل Gerfex. لا تنفذ أوامر."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read().decode("utf-8"))
        reply = data["choices"][0]["message"]["content"]
        return {
            "ok": True,
            "provider": provider.get("name", "openai_compatible"),
            "model": model,
            "reply": reply
        }
    except Exception as e:
        detail = str(e)
        try:
            if hasattr(e, "read"):
                detail += " | " + e.read().decode("utf-8", errors="replace")[:1200]
        except Exception:
            pass

        return {
            "ok": False,
            "provider": provider.get("name", "openai_compatible"),
            "model": model,
            "reply": "فشل اتصال النموذج الخارجي: " + detail
        }
