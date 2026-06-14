import json
import time
import uuid

from gerfex_android_paths import app_path

TRACE_FILE = app_path("runtime", "execution_trace.jsonl")
MAX_TRACES = 10


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_trace(goal):
    return {
        "trace_id": uuid.uuid4().hex[:12],
        "time": _now(),
        "goal": goal,
        "stages": []
    }


def add_stage(trace, stage, **data):
    if not isinstance(trace, dict):
        return trace

    trace.setdefault("stages", []).append({
        "time": _now(),
        "stage": stage,
        **data
    })
    return trace


def save_trace(trace):
    traces = []

    if TRACE_FILE.exists():
        try:
            for line in TRACE_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    traces.append(json.loads(line))
        except Exception:
            traces = []

    traces.append(trace)
    traces = traces[-MAX_TRACES:]

    TRACE_FILE.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in traces) + "\n",
        encoding="utf-8"
    )

    return str(TRACE_FILE)


def read_traces():
    if not TRACE_FILE.exists():
        return []
    out = []
    for line in TRACE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out[-MAX_TRACES:]
