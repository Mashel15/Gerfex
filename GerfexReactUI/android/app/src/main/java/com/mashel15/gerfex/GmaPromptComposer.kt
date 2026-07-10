package com.mashel15.gerfex

import android.content.Context
import android.util.Log
import java.util.concurrent.ConcurrentHashMap

object GmaPromptComposer {

    data class PromptPackage(
        val mode: String,
        val systemPrompt: String,
        val userPrompt: String
    )

    private const val BASE = "GerfexGMA/prompts"
    private const val MAX_SYSTEM_CHARS = 1400

    // الملفات صغيرة وتُقرأ مرة واحدة فقط خلال عمر التطبيق.
    private val assetCache = ConcurrentHashMap<String, String>()

    private fun readAsset(
        context: Context,
        relativePath: String,
        fallback: String
    ): String {
        return assetCache.getOrPut(relativePath) {
            try {
                context.assets.open("$BASE/$relativePath")
                    .bufferedReader(Charsets.UTF_8)
                    .use { it.readText().trim() }
                    .ifBlank { fallback }
            } catch (t: Throwable) {
                Log.w(
                    "GMA_DEBUG",
                    "Prompt asset fallback path=$relativePath error=${t.message}"
                )
                fallback
            }
        }
    }

    private fun detectMode(prompt: String): String {
        return when {
            prompt.contains("[LEARNING_SESSION]", ignoreCase = true) ->
                "learning"

            prompt.contains("[DEVELOPMENT_SESSION]", ignoreCase = true) ->
                "development"

            else ->
                "main"
        }
    }

    private fun cleanUserPrompt(prompt: String): String {
        return prompt
            .replace("[LEARNING_SESSION]", "", ignoreCase = true)
            .replace("[DEVELOPMENT_SESSION]", "", ignoreCase = true)
            .trim()
    }

    @JvmStatic
    fun compose(context: Context, prompt: String): PromptPackage {
        val mode = detectMode(prompt)

        val identity = readAsset(
            context,
            "identity/core_identity.txt",
            "أنت GMA، الذكاء الداخلي داخل Gerfex."
        )

        val mission = readAsset(
            context,
            "mission/core_mission.txt",
            "مهمتك دعم Gerfex بدقة ووضوح."
        )

        val behavior = readAsset(
            context,
            "behavior/response_behavior.txt",
            "أجب بالعربية مباشرة وباختصار، ولا تخمّن."
        )

        val modeInstruction = when (mode) {
            "learning" -> readAsset(
                context,
                "modes/learning.txt",
                "ناقش واقترح فقط، ولا تعتمد أي تعلم دون موافقة Mashel."
            )

            "development" -> readAsset(
                context,
                "modes/development.txt",
                "حلل المشكلة التقنية ولا تدّع تنفيذ شيء لم يُنفذ."
            )

            else -> readAsset(
                context,
                "modes/main.txt",
                "أجب عن السؤال مباشرة دون مقدمة طويلة."
            )
        }

        var systemPrompt = listOf(
            identity,
            mission,
            behavior,
            modeInstruction
        )
            .filter { it.isNotBlank() }
            .joinToString("\n")

        if (systemPrompt.length > MAX_SYSTEM_CHARS) {
            systemPrompt = systemPrompt.take(MAX_SYSTEM_CHARS)
            Log.w(
                "GMA_DEBUG",
                "GMA system prompt trimmed to $MAX_SYSTEM_CHARS chars"
            )
        }

        val cleanedPrompt = cleanUserPrompt(prompt)

        Log.i(
            "GMA_DEBUG",
            "GMA prompt composed mode=$mode system_len=${systemPrompt.length} user_len=${cleanedPrompt.length}"
        )

        return PromptPackage(
            mode = mode,
            systemPrompt = systemPrompt,
            userPrompt = cleanedPrompt
        )
    }
}
