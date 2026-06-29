import json
from datetime import datetime
from pathlib import Path

from GerfexIntegratedV1.gerfex_android_paths import app_path

REQUESTS_DIR = app_path("external_models", "requests")
TRACES_DIR = app_path("external_models", "traces")


def _now():
    return datetime.utcnow().isoformat() + "Z"


def receive_external_request(provider, capability, payload=None):
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    request = {
        "version": "EXTERNAL_MODEL_REQUEST_V1",
        "time": _now(),
        "provider": provider,
        "capability": capability,
        "payload": payload or {},
        "status": "received"
    }

    request_path = REQUESTS_DIR / f"{provider}_{capability}_request.json"
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "ok": False,
        "status": "denied_by_default",
        "reason": "External model capability requests require explicit Gerfex routing approval.",
        "request_path": str(request_path)
    }

    trace_path = TRACES_DIR / f"{provider}_{capability}_trace.json"
    trace_path.write_text(json.dumps({
        "request": request,
        "result": result
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    return result
