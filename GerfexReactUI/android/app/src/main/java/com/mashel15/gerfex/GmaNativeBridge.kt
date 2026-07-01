package com.mashel15.gerfex

import android.content.Context
import java.io.File
import com.arm.aichat.AiChat
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.runBlocking

object GmaNativeBridge {
    @JvmStatic
    fun generateBlocking(context: Context, modelPath: String, prompt: String, predictLength: Int = 256): String {
        return runBlocking {
            val modelFile = File(modelPath)
            if (!modelFile.exists()) {
                throw java.io.FileNotFoundException(modelFile.absolutePath)
            }

            val engine = AiChat.getInferenceEngine(context)
            engine.loadModel(modelFile.absolutePath)
            engine.setSystemPrompt("أنت GMA، الذكاء الداخلي الرسمي داخل Gerfex. أجب بالعربية وبشكل مختصر ومفيد.")
            val out = StringBuilder()
            engine.sendUserPrompt(prompt, predictLength).collect { token: String ->
                out.append(token)
            }
            out.toString()
        }
    }
}
