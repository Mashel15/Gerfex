import json
import time
import uuid
from gerfex_android_paths import app_path

TRACE_FILE = app_path("development", "trace", "execution_trace.jsonl")
PATH_FILE = app_path("development", "trace", "execution_path.jsonl")
MAX_TRACE_ITEMS = 10

def _iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def new_trace(goal):
    return {
        "trace_id": uuid.uuid4().hex[:12],
        "time": _iso(),
        "goal": goal,
        "stages": []
    }

def add_stage(trace, stage, source="", **kwargs):
    if not isinstance(trace, dict):
        return trace

    item = {
        "time": _iso(),
        "stage": stage,
        "source": source
    }
    item.update(kwargs)

    stages = trace.setdefault("stages", [])
    stages.append(item)
    return trace

def _read_jsonl(path):
    if not path.exists():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        return []
    return out

def _write_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)

    # Keep only the last 10 records, but store newest first.
    latest = items[-MAX_TRACE_ITEMS:]
    latest = list(reversed(latest))

    path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in latest) + ("\n" if latest else ""),
        encoding="utf-8"
    )

def _stage_line(stage):
    name = stage.get("stage", "-")
    source = stage.get("source", "-")

    extra = []
    for key in ["route", "provider", "intent", "target", "action", "ok", "reason"]:
        if key in stage and stage.get(key) not in [None, ""]:
            extra.append(f"{key}={stage.get(key)}")

    return f"{name} [{source}]" + ((" | " + " | ".join(extra)) if extra else "")

def build_execution_path(trace):
    stages = trace.get("stages", []) if isinstance(trace, dict) else []
    route = "-"
    decision = {}
    execution = {}

    for st in stages:
        if st.get("stage") == "brain_router":
            route = st.get("route", route)
        if st.get("stage") == "provider_response":
            decision = st
        if st.get("stage") in ["execution_observed", "execution_manager_end", "execution_manager_stop"]:
            execution = st

    ok_value = execution.get("execution_ok", execution.get("ok", False))

    return {
        "trace_id": trace.get("trace_id"),
        "time": trace.get("time"),
        "goal": trace.get("goal"),
        "route": route,
        "decision": {
            "intent": decision.get("intent"),
            "target": decision.get("target"),
            "reason": decision.get("reason")
        },
        "execution": {
            "ok": bool(ok_value),
            "reason": execution.get("reason"),
            "native_action_count": execution.get("native_action_count")
        },
        "path": [_stage_line(st) for st in stages]
    }

def save_trace(trace):
    traces = _read_jsonl(TRACE_FILE)
    traces.append(trace)
    _write_jsonl(TRACE_FILE, traces)

    paths = _read_jsonl(PATH_FILE)
    paths.append(build_execution_path(trace))
    _write_jsonl(PATH_FILE, paths)

    return trace
