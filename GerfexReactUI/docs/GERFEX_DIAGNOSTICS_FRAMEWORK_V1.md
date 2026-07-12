# Gerfex Diagnostics Framework V1

## Purpose

GDF is the permanent diagnostics infrastructure for Gerfex.
It traces requests across UI, Java, Python Core, routing, Android execution, JNI, model runtime, reply assembly, and verification.

## Core Rule

Every request receives one trace_id.
The same trace_id must pass through the complete request path without replacement.

UI -> Plugin -> Java Bridge -> Python Entry -> Gerfex Core -> Routing -> Internal Intelligence or Android Execution -> JNI -> Model Runtime -> Reply -> UI

## Stable Baseline

- Commit: f2dc964
- Tag: gma-stable-prompt-trace-20260713
- GMA native runtime is working.
- GmaPromptComposer remains disconnected.
- Long-answer completion is deferred to a future integrated improvement.

## Event Schema

Each diagnostic event contains:

- trace_id
- timestamp_utc
- layer
- stage
- status
- elapsed_ms when available
- safe details
- stable error_code when applicable

## Standard Layers

- ui
- plugin
- java_bridge
- python_entry
- core
- routing
- internal_intelligence
- android_execution
- jni
- model_runtime
- reply
- verification

## Status Values

- start
- ok
- warn
- error
- crash_boundary
- skipped
- timeout

## Runtime Storage

filesDir/gerfex_runtime_data/diagnostics/

Primary files:

- gdf_events.jsonl
- gdf_errors.jsonl
- gdf_last_trace.json
- gdf_runtime_state.json

Files must rotate automatically and tracing failures must never interrupt Gerfex.

## Privacy

Do not store full prompts, full replies, passwords, tokens, complete screen text, or complete memory content by default.

Allowed metadata includes character counts, token counts, route, provider, action type, elapsed time, stage, and error code.

## Crash Boundaries

A flushed crash_boundary event must be written before high-risk operations:

- native library loading
- model loading
- context creation
- prompt decoding
- generation
- native cleanup
- Android accessibility execution

The final persisted boundary identifies where a process crash most likely occurred.

## Implementation Order

1. Central Java and Python diagnostics infrastructure.
2. Plugin, Python Entry, Core, routing, and reply integration.
3. JNI and model runtime integration.
4. Android execution and verification integration.
5. Development Diagnostics viewer and export controls.

## Build Policy

- No build after every edit.
- Diagnostics must be included with the feature being changed.
- Review the complete bundle statically.
- Perform one intentional build only after the approved bundle is complete.

## Non-Goals

GDF V1 must not:

- change routing behavior
- reconnect GmaPromptComposer
- change generation length
- replace Execution Trace V1 immediately
- add Termux, Shizuku, or external-server dependencies
- change the active intelligence provider
- perform unrelated refactoring

## Approval

Status: APPROVED_FOR_IMPLEMENTATION
