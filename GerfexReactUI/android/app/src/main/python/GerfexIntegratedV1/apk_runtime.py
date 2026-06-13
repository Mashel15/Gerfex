import os

def is_apk_runtime():
    # Chaquopy / Android standalone mode marker.
    return True

def skip_external_runner_result(source="apk_runtime"):
    return {
        "ok": True,
        "skipped": True,
        "source": source,
        "reason": "APK runtime does not use Termux queue_runner. Actions are executed by native Android bridge."
    }
