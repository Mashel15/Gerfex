#include <jni.h>
#include <string>
#include <vector>
#include <android/log.h>

#include "llama.h"
#include "ggml-backend.h"

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "GMA_LLAMA", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "GMA_LLAMA", __VA_ARGS__)

static std::string jstr(JNIEnv *env, jstring s) {
    if (!s) return "";
    const char *c = env->GetStringUTFChars(s, nullptr);
    std::string out = c ? c : "";
    if (c) env->ReleaseStringUTFChars(s, c);
    return out;
}

extern "C"
JNIEXPORT jstring JNICALL
Java_com_mashel15_gerfex_GmaLlamaBridge_nativeGenerate(
        JNIEnv *env,
        jobject,
        jstring modelPath,
        jstring nativeLibDir,
        jstring systemPrompt,
        jstring userPrompt,
        jint predictLength
) {
    std::string model_path = jstr(env, modelPath);
    std::string native_lib_dir = jstr(env, nativeLibDir);
    std::string sys = jstr(env, systemPrompt);
    std::string user = jstr(env, userPrompt);

    LOGI("nativeGenerate start model=%s predict=%d", model_path.c_str(), (int) predictLength);

    try {
        llama_log_set([](enum ggml_log_level level, const char * text, void * user_data) {
            if (!text) return;
            switch (level) {
                case GGML_LOG_LEVEL_ERROR:
                    __android_log_print(ANDROID_LOG_ERROR, "GMA_LLAMA_LIB", "%s", text);
                    break;
                case GGML_LOG_LEVEL_WARN:
                    __android_log_print(ANDROID_LOG_WARN, "GMA_LLAMA_LIB", "%s", text);
                    break;
                case GGML_LOG_LEVEL_INFO:
                    __android_log_print(ANDROID_LOG_INFO, "GMA_LLAMA_LIB", "%s", text);
                    break;
                default:
                    __android_log_print(ANDROID_LOG_DEBUG, "GMA_LLAMA_LIB", "%s", text);
                    break;
            }
        }, nullptr);

        LOGI("nativeLibDir=%s", native_lib_dir.c_str());

        // في هذا البيلد لا نعتمد على libggml-cpu-*.so منفصل.
        // libllama/libggml المربوطين داخل التطبيق هم الباكند الفعلي.
        llama_backend_init();
        LOGI("llama_backend_init done");

        llama_model_params mparams = llama_model_default_params();
        mparams.use_mmap = true;
        mparams.use_mlock = false;
        mparams.check_tensors = false;

        llama_model *model = llama_model_load_from_file(model_path.c_str(), mparams);
        if (!model) {
            LOGE("llama_model_load_from_file returned null");
            return env->NewStringUTF("GMA_LLAMA_ERROR: model_load_null");
        }

        llama_context_params cparams = llama_context_default_params();
        cparams.n_ctx = 1024;
        cparams.n_batch = 128;
        cparams.n_ubatch = 128;
        cparams.n_threads = 4;
        cparams.n_threads_batch = 4;

        llama_context *ctx = llama_init_from_model(model, cparams);
        if (!ctx) {
            llama_model_free(model);
            LOGE("llama_init_from_model returned null");
            return env->NewStringUTF("GMA_LLAMA_ERROR: context_null");
        }

        const llama_vocab *vocab = llama_model_get_vocab(model);

        std::string prompt =
                "<start_of_turn>user\n" +
                sys + "\n\n" +
                user +
                "<end_of_turn>\n<start_of_turn>model\n";

        std::vector<llama_token> tokens(prompt.size() + 32);
        int32_t n_tokens = llama_tokenize(
                vocab,
                prompt.c_str(),
                (int32_t) prompt.size(),
                tokens.data(),
                (int32_t) tokens.size(),
                true,
                true
        );

        if (n_tokens < 0) {
            tokens.resize((size_t) (-n_tokens));
            n_tokens = llama_tokenize(
                    vocab,
                    prompt.c_str(),
                    (int32_t) prompt.size(),
                    tokens.data(),
                    (int32_t) tokens.size(),
                    true,
                    true
            );
        }

        if (n_tokens <= 0) {
            llama_free(ctx);
            llama_model_free(model);
            LOGE("tokenize failed n=%d", n_tokens);
            return env->NewStringUTF("GMA_LLAMA_ERROR: tokenize_failed");
        }

        llama_batch batch = llama_batch_init(n_tokens, 0, 1);
        for (int i = 0; i < n_tokens; ++i) {
            batch.token[i] = tokens[i];
            batch.pos[i] = i;
            batch.n_seq_id[i] = 1;
            batch.seq_id[i][0] = 0;
            batch.logits[i] = (i == n_tokens - 1);
        }
        batch.n_tokens = n_tokens;

        if (llama_decode(ctx, batch) != 0) {
            llama_batch_free(batch);
            llama_free(ctx);
            llama_model_free(model);
            LOGE("prompt decode failed");
            return env->NewStringUTF("GMA_LLAMA_ERROR: prompt_decode_failed");
        }

        llama_sampler *sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
        llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
        llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.9f, 1));
        llama_sampler_chain_add(sampler, llama_sampler_init_dist(1234));

        std::string out;
        int pos = n_tokens;

        int max_pred = predictLength > 0 ? predictLength : 128;
        if (max_pred > 256) max_pred = 256;

        for (int i = 0; i < max_pred; ++i) {
            llama_token tok = llama_sampler_sample(sampler, ctx, -1);
            llama_sampler_accept(sampler, tok);

            if (llama_vocab_is_eog(vocab, tok)) {
                break;
            }

            char piece[256];
            int n = llama_token_to_piece(vocab, tok, piece, sizeof(piece), 0, true);
            if (n > 0) out.append(piece, piece + n);

            llama_batch next = llama_batch_init(1, 0, 1);
            next.token[0] = tok;
            next.pos[0] = pos++;
            next.n_seq_id[0] = 1;
            next.seq_id[0][0] = 0;
            next.logits[0] = true;
            next.n_tokens = 1;

            if (llama_decode(ctx, next) != 0) {
                llama_batch_free(next);
                LOGE("decode failed during generation");
                break;
            }
            llama_batch_free(next);
        }

        llama_sampler_free(sampler);
        llama_batch_free(batch);
        llama_free(ctx);
        llama_model_free(model);

        if (out.empty()) {
            return env->NewStringUTF("GMA_LLAMA_EMPTY_REPLY");
        }

        LOGI("nativeGenerate done reply_len=%d", (int) out.size());
        return env->NewStringUTF(out.c_str());

    } catch (...) {
        LOGE("nativeGenerate unknown exception");
        return env->NewStringUTF("GMA_LLAMA_ERROR: native_exception");
    }
}
