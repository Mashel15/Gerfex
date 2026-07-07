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

        val cpuBackends = File(libDir).listFiles()
            ?.filter { it.isFile && it.name.startsWith("libggml-cpu-") && it.name.endsWith(".so") }
            ?.sortedBy { it.name }
            ?: emptyList()

        for (backend in cpuBackends) {
            if (tryLoadAbsolute(backend.name)) coreLoaded++
        }

        if (tryLoadAbsolute("libllama.so")) coreLoaded++
        if (tryLoadAbsolute("libllama-common.so")) coreLoaded++

        Log.i("GMA_DEBUG", "core native libs loaded count=" + coreLoaded)

        val jniLoaded = tryLoadAbsolute("libgerfex_llama_jni.so")
        Log.i("GMA_DEBUG", "jniLoaded=" + jniLoaded + " coreLoaded=" + coreLoaded)

        if (coreLoaded < 6) {
            setStage("llama_error_core_libs_incomplete")
            throw IllegalStateException("GMA native core libs incomplete. loaded=" + coreLoaded)
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
        try {
            setStage("llama_bridge_model_check")
            val modelFile = File(modelPath)
            if (!modelFile.exists()) {
                setStage("llama_bridge_model_missing")
                throw java.io.FileNotFoundException(modelFile.absolutePath)
            }

            loadNativeOnce(context)

            setStage("llama_native_generate_started")
            val systemPrompt =
                "أنت GMA، الذكاء الداخلي الرسمي داخل Gerfex. أجب بالعربية وبشكل مختصر ومفيد."

            val reply = nativeGenerate(
                modelFile.absolutePath,
                context.applicationInfo.nativeLibraryDir ?: "",
                systemPrompt,
                prompt,
                predictLength
            )

            setStage("llama_native_generate_done")
            return reply
        } catch (e: Throwable) {
            setStage("llama_error_${e.javaClass.simpleName}: ${e.message}")
            throw e
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
