# Gerfex Diagnostics Framework Foundation

This package contains the standalone Python foundation for GDF.

Current status:

- Creates unique `trace_id` values.
- Builds normalized diagnostic events.
- Writes JSONL events safely.
- Rotates diagnostic files.
- Records errors separately.
- Never intentionally interrupts the Gerfex execution path.
- Is not connected to Gerfex Runtime yet.

Runtime integration, routing changes, GMA changes, JNI changes, and APK
building are outside this foundation stage.
