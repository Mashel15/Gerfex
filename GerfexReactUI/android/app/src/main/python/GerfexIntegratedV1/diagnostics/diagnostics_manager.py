"""Public GDF diagnostics interface."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Mapping

from .event_writer import EventWriter
from .schemas import build_event
from .trace_id import create_trace_id


class DiagnosticsManager:
    """Central, failure-safe diagnostics manager."""

    def __init__(
        self,
        runtime_root: str | Path | None = None,
    ) -> None:
        self.writer = EventWriter(runtime_root)

    def new_trace_id(self) -> str:
        return create_trace_id()

    def event(
        self,
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
    ) -> bool:
        try:
            event = build_event(
                trace_id=trace_id,
                layer=layer,
                stage=stage,
                status=status,
                level=level,
                elapsed_ms=elapsed_ms,
                details=details,
                error_code=error_code,
                exception_type=exception_type,
            )
            return self.writer.write(event)
        except Exception:
            return False

    def start(
        self,
        *,
        trace_id: str,
        layer: str,
        stage: str,
        details: Mapping[str, Any] | None = None,
    ) -> float:
        self.event(
            trace_id=trace_id,
            layer=layer,
            stage=stage,
            status="start",
            details=details,
        )
        return time.monotonic()

    def finish(
        self,
        *,
        trace_id: str,
        layer: str,
        stage: str,
        started_at: float,
        details: Mapping[str, Any] | None = None,
    ) -> bool:
        elapsed_ms = (time.monotonic() - started_at) * 1000.0

        return self.event(
            trace_id=trace_id,
            layer=layer,
            stage=stage,
            status="ok",
            elapsed_ms=elapsed_ms,
            details=details,
        )

    def error(
        self,
        *,
        trace_id: str,
        layer: str,
        stage: str,
        error: BaseException | None = None,
        error_code: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> bool:
        return self.event(
            trace_id=trace_id,
            layer=layer,
            stage=stage,
            status="error",
            level="ERROR",
            details=details,
            error_code=error_code,
            exception_type=(
                type(error).__name__
                if error is not None
                else None
            ),
        )

    def crash_boundary(
        self,
        *,
        trace_id: str,
        layer: str,
        stage: str,
        details: Mapping[str, Any] | None = None,
    ) -> bool:
        return self.event(
            trace_id=trace_id,
            layer=layer,
            stage=stage,
            status="crash_boundary",
            level="INFO",
            details=details,
        )


diagnostics = DiagnosticsManager()
