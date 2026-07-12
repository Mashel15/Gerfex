"""Trace ID generation for Gerfex Diagnostics Framework."""

from __future__ import annotations

from datetime import datetime, timezone
import secrets


def create_trace_id() -> str:
    """Create a unique, filesystem-safe GDF trace ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    random_suffix = secrets.token_hex(3)
    return f"GDF-{timestamp}-{random_suffix}"
