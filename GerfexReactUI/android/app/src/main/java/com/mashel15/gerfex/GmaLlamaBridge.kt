package com.mashel15.gerfex

import android.content.Context
import android.util.Log
import java.io.File

object GmaLlamaBridge {
    @Volatile
    private var lastStage: String = "idle"

    @Volatile
    private var nativeLoaded: Boolean = false

    @JvmStatic
    fun getLastStage(): String = lastStage

    private fun setStage(stage: String) {
        lastStage = stage
    }


    private fun loadNativeOnce(context: Context) {
        if (nativeLoaded) return
        setStage("llama_jni_load_started")

        val libDir = context.applicationInfo.nativeLibraryDir ?: ""
        Log.i("GMA_DEBUG", "nativeLibraryDir=$libDir")

        fun tryLoadAbsolute(libFileName: String): Boolean {
            return try {
                val f = File(libDir, libFileName)
                if (!f.exists()) {
                    Log.w("GMA_DEBUG", "native lib missing: " + f.absolutePath)
                    false
                } else {
                    Log.i("GMA_DEBUG", "loading native lib: " + f.absolutePath)
                    System.load(f.absolutePath)
                    Log.i("GMA_DEBUG", "loaded native lib: " + f.name)
                    true
                }
            } catch (t: Throwable) {
                Log.e("GMA_DEBUG", "failed loading native lib: $libFileName", t)
                false
            }
        }

        var coreLoaded = 0
        if (tryLoadAbsolute("libomp.so")) coreLoaded++
        if (tryLoadAbsolute("libggml-base.so")) coreLoaded++
        if (tryLoadAbsolute("libggml.so")) coreLoaded++
        if (tryLoadAbsolute("libllama.so")) coreLoaded++
        if (tryLoadAbsolute("libllama-common.so")) coreLoaded++

        Log.i("GMA_DEBUG", "core native libs loaded count=" + coreLoaded)

        var backendLoaded = 0
        try {
            val dir = File(libDir)
            val cpuLibs = dir.listFiles()
                ?.filter { it.isFile && it.name.startsWith("libggml-cpu-") && it.name.endsWith(".so") }
                ?.sortedBy { it.name }
                ?: emptyList()

            Log.i("GMA_DEBUG", "detected ggml cpu libs count=" + cpuLibs.size)
            for (f in cpuLibs) {
                try {
                    Log.i("GMA_DEBUG", "loading detected cpu backend: " + f.absolutePath)
                    System.load(f.absolutePath)
                    Log.i("GMA_DEBUG", "loaded detected cpu backend: " + f.name)
                    backendLoaded++
                } catch (t: Throwable) {
                    Log.e("GMA_DEBUG", "failed detected cpu backend: " + f.name, t)
                }
            }
        } catch (t: Throwable) {
            Log.e("GMA_DEBUG", "failed while scanning nativeLibraryDir", t)
        }

        val jniLoaded = tryLoadAbsolute("libgerfex_llama_jni.so")
        Log.i("GMA_DEBUG", "jniLoaded=" + jniLoaded + " backendLoaded=" + backendLoaded + " coreLoaded=" + coreLoaded)

        if (coreLoaded < 5) {
            setStage("llama_error_core_libs_incomplete")
            throw IllegalStateException("GMA native core libs incomplete. loaded=" + coreLoaded)
        }
        if (backendLoaded < 1) {
            setStage("llama_error_no_cpu_backend_loaded")
            throw IllegalStateException("GMA no ggml cpu backend loaded from nativeLibraryDir=" + libDir)
        }
        if (!jniLoaded) {
            setStage("llama_error_jni_not_loaded")
            throw IllegalStateException("GMA JNI bridge failed to load")
        }

        nativeLoaded = true
        setStage("llama_jni_loaded")
    }


    @JvmStatic
    fun generateBlocking(
        context: Context,
        modelPath: String,
        prompt: String,
        predictLength: Int = 256
    ): String {
        fun runtimeTrace(stage: String, detail: String = "") {
            try {
                val runtimeDir = File(
                    context.filesDir,
                    "gerfex_runtime_data/runtime"
                )
                runtimeDir.mkdirs()

                val traceFile = File(
                    runtimeDir,
                    "gma_runtime_trace.txt"
                )

                // Prevent the trace file from growing without limit.
                if (traceFile.exists() && traceFile.length() > 512 * 1024) {
                    val tail = traceFile
                        .readText(Charsets.UTF_8)
                        .takeLast(256 * 1024)

                    traceFile.writeText(
                        tail,
                        Charsets.UTF_8
                    )
                }

                val safeDetail = detail
                    .replace("\n", " ")
                    .replace("\r", " ")
                    .take(1000)

                traceFile.appendText(
                    "${System.currentTimeMillis()} " +
                        "stage=$stage detail=$safeDetail\n",
                    Charsets.UTF_8
                )

                Log.i(
                    "GERFEX_GMA_RUNTIME",
                    "stage=$stage detail=$safeDetail"
                )
            } catch (_: Throwable) {
                // Tracing must never interrupt GMA runtime.
            }
        }

        runtimeTrace(
            "bridge_enter",
            "predict=$predictLength " +
                "prompt_chars=${prompt.length} " +
                "model_path=$modelPath"
        )

        try {
            setStage("llama_bridge_model_check")
            runtimeTrace("model_check_start")

            val modelFile = File(modelPath)

            if (!modelFile.exists()) {
                setStage("llama_bridge_model_missing")

                runtimeTrace(
                    "model_check_missing",
                    modelFile.absolutePath
                )

                throw java.io.FileNotFoundException(
                    modelFile.absolutePath
                )
            }

            runtimeTrace(
                "model_check_ok",
                "model_size=${modelFile.length()}"
            )

            runtimeTrace("jni_load_start")
            loadNativeOnce(context)
            runtimeTrace(
                "jni_load_done",
                "native_library_dir=" +
                    (context.applicationInfo.nativeLibraryDir ?: "")
            )

            setStage("llama_native_generate_started")

            // Stable native prompt path.
            // GmaPromptComposer remains disconnected from runtime.
            val systemPrompt =
                "أنت GMA، الذكاء الداخلي الرسمي داخل Gerfex. أجب بالعربية وبشكل مختصر ومفيد."

            runtimeTrace(
                "native_call_enter",
                "system_chars=${systemPrompt.length} " +
                    "user_chars=${prompt.length} " +
                    "predict=$predictLength"
            )

            val reply = nativeGenerate(
                modelFile.absolutePath,
                context.applicationInfo.nativeLibraryDir ?: "",
                systemPrompt,
                prompt,
                predictLength
            )

            runtimeTrace(
                "native_call_return",
                "reply_chars=${reply.length}"
            )

            setStage("llama_native_generate_done")
            runtimeTrace(
                "bridge_done",
                "reply_chars=${reply.length}"
            )

            return reply
        } catch (error: Throwable) {
            val errorDetail =
                "${error.javaClass.name}: ${error.message ?: "no_message"}"

            setStage(
                "llama_error_${error.javaClass.simpleName}: ${error.message}"
            )

            runtimeTrace(
                "bridge_exception",
                errorDetail
            )

            throw error
        }
    }

    @JvmStatic
    private external fun nativeGenerate(
        modelPath: String,
        nativeLibDir: String,
        systemPrompt: String,
        userPrompt: String,
        predictLength: Int
    ): String
}
