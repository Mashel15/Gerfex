"""Adapter between Execution Trace V1 data and GDF events.

This module is standalone and is not connected to Gerfex runtime yet.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .diagnostics_manager import DiagnosticsManager


_STAGE_STATUS_MAP = {
    "exception": "error",
    "error": "error",
    "failed": "error",
    "timeout": "timeout",
    "skipped": "skipped",
}


def _safe_text(value: Any, limit: int = 300) -> str:
    """Return a compact single-line string."""
    return (
        str(value)
        .replace("\n", " ")
        .replace("\r", " ")
        [:limit]
    )


def _resolve_status(stage: Mapping[str, Any]) -> str:
    """Infer a GDF status without changing the source trace."""
    name = str(stage.get("stage", "")).lower()

    for marker, status in _STAGE_STATUS_MAP.items():
        if marker in name:
            return status

    if stage.get("ok") is False:
        return "error"

    if stage.get("execution_ok") is False:
        return "error"

    return "ok"


def _resolve_layer(stage: Mapping[str, Any]) -> str:
    """Map an Execution Trace source to a generic GDF layer."""
    source = str(stage.get("source", "")).lower()

    if "gerfex_entry" in source:
        return "python_entry"
    if "gerfex_core" in source:
        return "core"
    if "router" in source:
        return "routing"
    if "brain" in source or "provider" in source:
        return "internal_intelligence"
    if "execution" in source:
        return "android_execution"
    if "memory" in source:
        return "core"

    return "core"


def _stage_details(stage: Mapping[str, Any]) -> dict[str, Any]:
    """Extract safe metadata while excluding large or sensitive values."""
    allowed_keys = (
        "source",
        "route",
        "provider",
        "intent",
        "target",
        "action",
        "ok",
        "execution_ok",
        "reason",
        "result_type",
        "native_action_count",
        "advisors",
        "mode",
    )

    details: dict[str, Any] = {}

    for key in allowed_keys:
        if key not in stage:
            continue

        value = stage.get(key)

        if value is None:
            continue

        if isinstance(value, (bool, int, float)):
            details[key] = value
        else:
            details[key] = _safe_text(value)

    return details


def build_stage_event(
    trace: Mapping[str, Any],
    stage: Mapping[str, Any],
) -> dict[str, Any]:
    """Convert one Execution Trace stage into GDF event arguments."""
    return {
        "trace_id": str(trace.get("trace_id", "")),
        "layer": _resolve_layer(stage),
        "stage": str(stage.get("stage", "unknown_stage")),
        "status": _resolve_status(stage),
        "level": (
            "ERROR"
            if _resolve_status(stage) in {"error", "timeout"}
            else "INFO"
        ),
        "details": _stage_details(stage),
        "error_code": (
            "execution_trace_stage_error"
            if _resolve_status(stage) == "error"
            else None
        ),
    }


def iter_stage_events(
    trace: Mapping[str, Any],
) -> Iterable[dict[str, Any]]:
    """Yield converted GDF event arguments in original stage order."""
    stages = trace.get("stages", [])

    if not isinstance(stages, list):
        return

    for stage in stages:
        if isinstance(stage, Mapping):
            yield build_stage_event(trace, stage)


def export_trace(
    trace: Mapping[str, Any],
    manager: DiagnosticsManager,
) -> int:
    """Export one trace to GDF and return successful event count."""
    if not isinstance(trace, Mapping):
        return 0

    trace_id = str(trace.get("trace_id", "")).strip()

    if not trace_id:
        return 0

    written = 0

    for event in iter_stage_events(trace):
        if manager.event(**event):
            written += 1

    return written


def safe_export_trace(
    trace: Mapping[str, Any],
    manager: DiagnosticsManager,
) -> int:
    """Failure-safe export which must never interrupt Gerfex."""
    try:
        return export_trace(trace, manager)
    except Exception:
        return 0
