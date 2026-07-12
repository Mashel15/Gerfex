"""Gerfex Diagnostics Framework (GDF) foundation."""

from .diagnostics_manager import DiagnosticsManager, diagnostics
from .trace_id import create_trace_id

__all__ = [
    "DiagnosticsManager",
    "diagnostics",
    "create_trace_id",
]
