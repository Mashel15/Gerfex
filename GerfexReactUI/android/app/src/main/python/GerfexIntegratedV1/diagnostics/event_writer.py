"""Safe JSONL event persistence for GDF."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class EventWriter:
    """Persist GDF events without interrupting Gerfex on failure."""

    def __init__(
        self,
        runtime_root: str | Path | None = None,
        *,
        events_limit_bytes: int = 2 * 1024 * 1024,
        errors_limit_bytes: int = 1 * 1024 * 1024,
    ) -> None:
        self.runtime_root = (
            Path(runtime_root)
            if runtime_root is not None
            else Path("gerfex_runtime_data") / "diagnostics"
        )
        self.events_limit_bytes = events_limit_bytes
        self.errors_limit_bytes = errors_limit_bytes

    def _ensure_root(self) -> None:
        self.runtime_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _rotate(path: Path, limit_bytes: int) -> None:
        if not path.exists() or path.stat().st_size <= limit_bytes:
            return

        keep_bytes = max(limit_bytes // 2, 64 * 1024)

        with path.open("rb") as handle:
            handle.seek(max(0, path.stat().st_size - keep_bytes))
            tail = handle.read()

        newline_index = tail.find(b"\n")
        if newline_index >= 0:
            tail = tail[newline_index + 1 :]

        path.write_bytes(tail)

    def _append_jsonl(
        self,
        path: Path,
        event: Mapping[str, Any],
        limit_bytes: int,
    ) -> None:
        self._rotate(path, limit_bytes)

        serialized = json.dumps(
            dict(event),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        with path.open("a", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.write("\n")
            handle.flush()

    def write(self, event: Mapping[str, Any]) -> bool:
        """Write an event safely. Return False rather than raise."""
        try:
            self._ensure_root()

            events_path = self.runtime_root / "gdf_events.jsonl"
            self._append_jsonl(
                events_path,
                event,
                self.events_limit_bytes,
            )

            status = str(event.get("status", "")).lower()
            level = str(event.get("level", "")).upper()

            if status in {"error", "crash_boundary", "timeout"} or level == "ERROR":
                errors_path = self.runtime_root / "gdf_errors.jsonl"
                self._append_jsonl(
                    errors_path,
                    event,
                    self.errors_limit_bytes,
                )

            last_trace_path = self.runtime_root / "gdf_last_trace.json"
            last_trace_path.write_text(
                json.dumps(
                    dict(event),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            return True
        except Exception:
            return False
