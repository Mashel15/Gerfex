#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "===== INSTALLED GMA NATIVE LIBS ====="
~/rish/rish -c 'APPDIR=$(pm path com.mashel15.gerfex | head -1 | sed "s#package:##" | sed "s#/base.apk##"); echo "APPDIR=$APPDIR"; find "$APPDIR/lib/arm64" -maxdepth 1 -type f | grep -E "libllama|libggml|libomp" | sort'

echo
echo "===== INSTALLED DIAGNOSTIC STRINGS ====="
~/rish/rish -c 'APPDIR=$(pm path com.mashel15.gerfex | head -1 | sed "s#package:##" | sed "s#/base.apk##"); strings "$APPDIR/lib/arm64/libgerfex_llama_jni.so" | grep -E "GMA_LLAMA_ERROR: model_load_null|llama_log=%s|ggml_backend_load_all called"'

echo
echo "===== APP MODEL FILE CHECK ====="
~/rish/rish -c 'run-as com.mashel15.gerfex sh -c '"'"'
f=files/GerfexModels/google_gemma-3-4b-it-Q2_K.gguf
ls -lh "$f"
dd if="$f" bs=1 count=16 2>/dev/null | od -An -tx1
'"'"''

echo
echo "===== SEARCH SAVED GMA ERRORS ====="
~/rish/rish -c 'run-as com.mashel15.gerfex sh -c '"'"'
grep -RIn "GMA_LLAMA_ERROR\|llama_log\|model_load_null\|surface_native_reply_error" files 2>/dev/null | tail -80 || true
'"'"''
