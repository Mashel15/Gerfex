import json, time, uuid
from datetime import datetime
from GerfexIntegratedV1.gerfex_android_paths import app_path

TRACE_FILE = app_path("development", "trace", "execution_trace.jsonl")
PATH_FILE = app_path("development", "trace", "execution_path.jsonl")
MAX_TRACE_ITEMS = 10
DEDUP_SECONDS = 3

def _iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _ts(x):
    try:
        return datetime.strptime(x.get("time", ""), "%Y-%m-%dT%H:%M:%SZ").timestamp()
    except Exception:
        return 0

def new_trace(goal):
    return {"trace_id": uuid.uuid4().hex[:12], "time": _iso(), "goal": goal, "stages": []}

def add_stage(trace, stage, source="", **kwargs):
    if not isinstance(trace, dict):
        return trace
    item = {"time": _iso(), "stage": stage, "source": source}
    item.update(kwargs)
    trace.setdefault("stages", []).append(item)
    return trace

def _read_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def _write_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(items, key=_ts)
    items = items[-MAX_TRACE_ITEMS:]
    items = list(reversed(items))
    path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in items) + ("\n" if items else ""),
        encoding="utf-8"
    )

def _is_duplicate(items, item):
    if not items:
        return False
    latest = sorted(items, key=_ts)[-1]
    return (
        latest.get("goal") == item.get("goal")
        and abs(_ts(item) - _ts(latest)) <= DEDUP_SECONDS
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
    route, decision, execution = "-", {}, {}
    for st in stages:
        stage_name = st.get("stage")

        if stage_name == "brain_router":
            route = st.get("route", route)

        if stage_name == "main_surface_done" and st.get("path") == "gerfex_brain":
            route = "gma_native"

        if stage_name in ["surface_native_requested", "surface_native_bridge_start"]:
            route = "gma_native"

        if stage_name == "surface_native_done":
            route = "gma_native"
            execution = {
                "ok": True,
                "reason": "GMA native reply generated",
                "native_action_count": 0,
            }

        if stage_name == "surface_native_reply_error":
            route = "gma_native"
            execution = {
                "ok": False,
                "reason": st.get("error_code") or st.get("reason") or "GMA native error",
                "native_action_count": 0,
            }

        if stage_name == "provider_response":
            decision = st

        if stage_name in ["execution_observed", "execution_manager_end", "execution_manager_stop"]:
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
    if _is_duplicate(traces, trace):
        return trace
    traces.append(trace)
    _write_jsonl(TRACE_FILE, traces)

    paths = _read_jsonl(PATH_FILE)
    paths.append(build_execution_path(trace))
    _write_jsonl(PATH_FILE, paths)
    return trace
