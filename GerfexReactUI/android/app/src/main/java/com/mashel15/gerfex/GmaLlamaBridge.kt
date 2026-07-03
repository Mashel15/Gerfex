package com.mashel15.gerfex

import android.content.Context
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

    private fun loadNativeOnce() {
        if (nativeLoaded) return
        setStage("llama_jni_load_started")
        for (lib in listOf(
            "omp",
            "ggml-base",
            "ggml",
            "ggml-cpu-android_armv8.0_1",
            "ggml-cpu-android_armv8.2_1",
            "ggml-cpu-android_armv8.2_2",
            "ggml-cpu-android_armv8.6_1",
            "ggml-cpu-android_armv9.0_1",
            "ggml-cpu-android_armv9.2_1",
            "ggml-cpu-android_armv9.2_2",
            "llama",
            "llama-common"
        )) {
            try {
                System.loadLibrary(lib)
            } catch (_: Throwable) {
            }
        }
        System.loadLibrary("gerfex_llama_jni")
        nativeLoaded = true
        setStage("llama_jni_loaded")
    }

    @JvmStatic
    fun generateBlocking(context: Context, modelPath: String, prompt: String, predictLength: Int = 256): String {
        try {
            setStage("llama_bridge_model_check")

            val modelFile = File(modelPath)
            if (!modelFile.exists()) {
                setStage("llama_bridge_model_missing")
                throw java.io.FileNotFoundException(modelFile.absolutePath)
            }

            loadNativeOnce()

            setStage("llama_native_generate_started")

            val systemPrompt =
                "أنت GMA، الذكاء الداخلي الرسمي داخل Gerfex. أجب بالعربية وبشكل مختصر ومفيد."

            val reply = nativeGenerate(
                modelFile.absolutePath,
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
        systemPrompt: String,
        userPrompt: String,
        predictLength: Int
    ): String
}
