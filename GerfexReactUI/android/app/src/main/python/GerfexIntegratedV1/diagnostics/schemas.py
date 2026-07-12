"""Shared GDF event schema helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

VALID_STATUSES = frozenset({
    "start",
    "ok",
    "warn",
    "error",
    "crash_boundary",
    "skipped",
    "timeout",
})

VALID_LEVELS = frozenset({
    "ERROR",
    "WARN",
    "INFO",
    "DEBUG",
    "VERBOSE",
})


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def sanitize_details(
    details: Mapping[str, Any] | None,
    *,
    max_string_length: int = 1000,
) -> dict[str, Any]:
    """Create a JSON-safe, size-limited details dictionary."""
    if not details:
        return {}

    safe: dict[str, Any] = {}

    for key, value in details.items():
        safe_key = str(key)[:100]

        if value is None or isinstance(value, (bool, int, float)):
            safe[safe_key] = value
        elif isinstance(value, str):
            safe[safe_key] = (
                value.replace("\n", " ")
                .replace("\r", " ")
                [:max_string_length]
            )
        else:
            safe[safe_key] = str(value)[:max_string_length]

    return safe


def build_event(
    *,
    trace_id: str,
    layer: str,
    stage: str,
    status: str,
    level: str = "INFO",
    elapsed_ms: float | None = None,
    details: Mapping[str, Any] | None = None,
    error_code: str | None = None,
    exception_type: str | None = None,
) -> dict[str, Any]:
    """Build one validated GDF event."""
    normalized_status = str(status).lower()
    normalized_level = str(level).upper()

    if normalized_status not in VALID_STATUSES:
        normalized_status = "warn"

    if normalized_level not in VALID_LEVELS:
        normalized_level = "INFO"

    event: dict[str, Any] = {
        "trace_id": str(trace_id),
        "timestamp_utc": utc_timestamp(),
        "layer": str(layer),
        "stage": str(stage),
        "status": normalized_status,
        "level": normalized_level,
        "details": sanitize_details(details),
    }

    if elapsed_ms is not None:
        event["elapsed_ms"] = max(0.0, round(float(elapsed_ms), 3))

    if error_code:
        event["error_code"] = str(error_code)[:200]

    if exception_type:
        event["exception_type"] = str(exception_type)[:300]

    return event
