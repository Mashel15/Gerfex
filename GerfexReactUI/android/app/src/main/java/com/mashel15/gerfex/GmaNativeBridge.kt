package com.mashel15.gerfex

import android.content.Context
import java.io.File
import com.arm.aichat.AiChat
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.runBlocking

object GmaNativeBridge {
    @Volatile
    private var lastStage: String = "idle"

    @Volatile
    private var backendInitTried: Boolean = false

    private fun tryLoadBackend(lib: String): Boolean {
        return try {
            System.loadLibrary(lib)
            true
        } catch (_: Throwable) {
            false
        }
    }

    private fun ensureNativeBackends() {
        if (backendInitTried) return
        backendInitTried = true
        setStage("backend_load_started")

        val loaded = linkedMapOf<String, Boolean>()
        for (name in listOf(
            "omp",
            "ggml-base",
            "ggml",
            "ggml-cpu-android_armv8.0_1",
            "ggml-cpu-android_armv8.2_1",
            "ggml-cpu-android_armv8.2_2",
            "llama",
            "llama-common",
            "ai-chat"
        )) {
            loaded[name] = tryLoadBackend(name)
        }

        setStage("backend_load_result_" + loaded.entries.joinToString(",") { it.key + "=" + it.value })
        if (!loaded.values.any { it }) {
            throw IllegalStateException("No native backend library could be loaded: " + loaded)
        }
    }

    @JvmStatic
    fun getLastStage(): String = lastStage

    private fun setStage(stage: String) {
        lastStage = stage
    }

    @JvmStatic
    fun generateBlocking(context: Context, modelPath: String, prompt: String, predictLength: Int = 256): String {
        return runBlocking {
            try {
                setStage("bridge_model_check")
                val modelFile = File(modelPath)
                if (!modelFile.exists()) {
                    setStage("bridge_model_missing")
                    throw java.io.FileNotFoundException(modelFile.absolutePath)
                }

                ensureNativeBackends()

                setStage("load_started")
                val engine = AiChat.getInferenceEngine(context)
                engine.loadModel(modelFile.absolutePath)
                setStage("load_done")

                engine.setSystemPrompt("أنت GMA، الذكاء الداخلي الرسمي داخل Gerfex. أجب بالعربية وبشكل مختصر ومفيد.")
                val out = StringBuilder()

                setStage("prompt_started")
                var tokenCount = 0
                engine.sendUserPrompt(prompt, predictLength).collect { token: String ->
                    if (tokenCount == 0) setStage("first_token")
                    tokenCount += 1
                    out.append(token)
                }

                setStage("done_tokens_$tokenCount")
                out.toString()
            } catch (e: Exception) {
                setStage("error_${e.javaClass.simpleName}: ${e.message}")
                throw e
            }
        }
    }
}
