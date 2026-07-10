package com.mashel15.gerfex

import android.content.Context
import android.util.Log

object GmaPromptComposer {

    private const val TAG = "GMA_DEBUG"
    private const val PROMPT_ROOT = "GerfexGMA/prompts"

    data class PromptPackage(
        val mode: String,
        val systemPrompt: String,
        val userPrompt: String
    )

    private fun readAsset(
        context: Context,
        relativePath: String,
        fallback: String
    ): String {
        val fullPath = "$PROMPT_ROOT/$relativePath"

        return try {
            context.assets
                .open(fullPath)
                .bufferedReader(Charsets.UTF_8)
                .use { it.readText().trim() }
                .ifBlank { fallback }
        } catch (error: Throwable) {
            Log.w(
                TAG,
                "Prompt asset unavailable: $fullPath; using fallback",
                error
            )
            fallback
        }
    }

    private fun detectMode(prompt: String): String {
        return when {
            prompt.contains(
                "[LEARNING_SESSION]",
                ignoreCase = true
            ) -> "learning"

            prompt.contains(
                "[DEVELOPMENT_SESSION]",
                ignoreCase = true
            ) -> "development"

            else -> "main"
        }
    }

    private fun cleanUserPrompt(prompt: String): String {
        return prompt
            .replace(
                "[LEARNING_SESSION]",
                "",
                ignoreCase = true
            )
            .replace(
                "[DEVELOPMENT_SESSION]",
                "",
                ignoreCase = true
            )
            .trim()
    }

    private fun composeLearningInstructions(
        context: Context
    ): String {
        val learningMode = readAsset(
            context,
            "modes/learning.txt",
            "ناقش واقترح فقط، ولا تعتمد أي تعلم دون موافقة Mashel."
        )

        val constitution = readAsset(
            context,
            "learning/constitution/learning_constitution.txt",
            "صفحة التعلم للنقاش والاقتراح، والاعتماد بيد Mashel."
        )

        val behavior = readAsset(
            context,
            "learning/personality_behavior/learning_behavior.txt",
            "ناقش بوضوح، ولا تخمّن، ولا تكرر هويتك."
        )

        val developerRole = readAsset(
            context,
            "learning/developer_role/developer_role.txt",
            "حلل Gerfex واقترح حلولًا، ولا تدّع تنفيذ شيء لم يحدث."
        )

        val governance = readAsset(
            context,
            "learning/governance/approval_policy.txt",
            "كل تعلم يبقى مقترحًا حتى اعتماد Mashel الصريح."
        )

        val sessionPolicy = readAsset(
            context,
            "learning/session/learning_session_policy.txt",
            "ركز على موضوع الجلسة، ولا تنفذ أوامر Android من صفحة التعلم."
        )

        return listOf(
            learningMode,
            constitution,
            behavior,
            developerRole,
            governance,
            sessionPolicy
        )
            .filter { it.isNotBlank() }
            .joinToString("\n\n")
    }

    @JvmStatic
    fun compose(
        context: Context,
        prompt: String
    ): PromptPackage {
        val mode = detectMode(prompt)
        val cleanedPrompt = cleanUserPrompt(prompt)

        val identity = readAsset(
            context,
            "identity/core_identity.txt",
            "GMA هو الذكاء الداخلي العامل خلف Gerfex."
        )

        val mission = readAsset(
            context,
            "mission/core_mission.txt",
            "مهمتك مساعدة Gerfex وMashel بدقة وصدق."
        )

        val behavior = readAsset(
            context,
            "behavior/response_behavior.txt",
            "أجب بالعربية بوضوح واختصار، ولا تخمّن."
        )

        val modeInstructions = when (mode) {
            "learning" -> composeLearningInstructions(context)

            "development" -> readAsset(
                context,
                "modes/development.txt",
                "حلل المشكلات التقنية واقترح حلولًا قابلة للمراجعة."
            )

            else -> readAsset(
                context,
                "modes/main.txt",
                "أجب مباشرة باسم Gerfex دون تكرار هوية GMA."
            )
        }

        val systemPrompt = listOf(
            identity,
            mission,
            behavior,
            modeInstructions
        )
            .filter { it.isNotBlank() }
            .joinToString("\n\n")

        return PromptPackage(
            mode = mode,
            systemPrompt = systemPrompt,
            userPrompt = cleanedPrompt
        )
    }
}
