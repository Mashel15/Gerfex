#!/data/data/com.termux/files/usr/bin/bash
set -e

PKG=com.mashel15.gerfex

echo "===== 1 INSTALLED APK PATH ====="
~/rish/rish -c 'pm path com.mashel15.gerfex'

echo
echo "===== 2 INSTALLED NATIVE LIBS ====="
~/rish/rish -c 'APPDIR=$(pm path com.mashel15.gerfex | head -1 | sed "s#package:##" | sed "s#/base.apk##"); echo "APPDIR=$APPDIR"; find "$APPDIR/lib/arm64" -maxdepth 1 -type f | sort'

echo
echo "===== 3 JNI DIAGNOSTIC STRINGS ====="
~/rish/rish -c 'APPDIR=$(pm path com.mashel15.gerfex | head -1 | sed "s#package:##" | sed "s#/base.apk##"); strings "$APPDIR/lib/arm64/libgerfex_llama_jni.so" | grep -E "GMA_LLAMA_ERROR|ggml_backend_load_all|llama_backend_init|model_load_null|nativeLibDir|llama_log" || true'

echo
echo "===== 4 MODEL FILE CHECK ====="
~/rish/rish -c 'run-as com.mashel15.gerfex sh -c '"'"'
f=files/GerfexModels/google_gemma-3-4b-it-Q2_K.gguf
echo "MODEL=$f"
ls -lh "$f" || true
echo "HEAD16:"
dd if="$f" bs=1 count=16 2>/dev/null | od -An -tx1 || true
'"'"''

echo
echo "===== 5 SAVED APP ERRORS ====="
~/rish/rish -c 'run-as com.mashel15.gerfex sh -c '"'"'
grep -RIn "GMA_LLAMA_ERROR\|llama_log\|model_load_null\|context_null\|tokenize_failed\|prompt_decode_failed\|surface_native_reply_error" files 2>/dev/null | tail -120 || true
'"'"''

echo
echo "===== 6 LOGCAT SNAPSHOT GMA ONLY ====="
~/rish/rish -c 'logcat -d -t 5000 | grep -E "GMA_LLAMA|GMA_LLAMA_LIB|GMA_DEBUG|GerfexPlugin|GmaLlamaBridge" | tail -300 || true'

echo
echo "===== 7 PACKAGE NATIVE DIR FROM DUMPSYS ====="
~/rish/rish -c 'dumpsys package com.mashel15.gerfex | grep -iE "nativeLibraryDir|primaryCpuAbi|versionName|versionCode" || true'

echo
echo "===== DONE ====="
