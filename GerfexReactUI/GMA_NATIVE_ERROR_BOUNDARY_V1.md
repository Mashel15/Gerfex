# GMA Native Error Boundary V1

## Purpose

This document defines the first structured error boundary for the official GMA Native route.

Official GMA route:

App.jsx
-> GerfexPlugin.gmaNativeChat()
-> GmaLlamaBridge.kt
-> gerfex_llama_jni.cpp
-> llama/ggml
-> GGUF

## Problem

Before this boundary, some native/runtime failures could return as plain reply text.

That made errors look like normal GMA chat responses.

Examples:
- GMA_LLAMA_ERROR
- GMA_LLAMA_EMPTY_REPLY
- no_backend_loaded
- model_load_null
- context_null

## Plugin behavior

GerfexPlugin.java now checks the reply returned from GmaLlamaBridge.generateBlocking.

If the reply is empty or contains a known native error marker, gmaNativeChat returns:

- ok=false
- stage=native_reply_error
- error_code=<detected error>
- error=<raw native reply text>
- reply=""

Normal valid replies still return:

- ok=true
- stage=done
- reply=<GMA response>

## App behavior

App.jsx now checks nativeGma.ok.

If nativeGma.ok is false, the UI shows the message as a Gerfex system/native error:

خطأ في GMA Native: <error_code>

It no longer displays raw native errors as if they were normal GMA replies.

## Scope

This change does not modify:

- JNI generation logic
- GmaLlamaBridge.kt
- llama/ggml loading
- Python Core
- routing classifier
- UI design

## Build policy

No APK build is required immediately after this single change.

This change is part of a grouped architecture stabilization batch and should be built later only when enough changes are accumulated or when Mashel decides the batch is ready.
