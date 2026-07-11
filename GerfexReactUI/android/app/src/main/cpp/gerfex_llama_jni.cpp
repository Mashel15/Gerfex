#include <jni.h>
#include <string>
#include <vector>
#include <android/log.h>
#include <filesystem>
#include <chrono>
#include <atomic>

#include "llama.h"
#include <mutex>
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


// GMA persistent runtime:
// Keep the model loaded between requests.
// Context remains request-scoped for safety.
static std::mutex g_gma_runtime_mutex;
static llama_model *g_gma_cached_model = nullptr;
static std::string g_gma_cached_model_path;
static bool g_gma_backend_initialized = false;
static std::atomic<uint64_t> g_gma_request_counter{0};

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

    const uint64_t request_id = ++g_gma_request_counter;

    LOGI(
            "GMA_TRACK request_start id=%llu model=%s "
            "system_chars=%d user_chars=%d predict=%d",
            (unsigned long long) request_id,
            model_path.c_str(),
            (int) sys.size(),
            (int) user.size(),
            (int) predictLength
    );

    LOGI("nativeGenerate start model=%s predict=%d",
         model_path.c_str(), (int) predictLength);

    std::lock_guard<std::mutex> runtime_lock(g_gma_runtime_mutex);

    LOGI(
            "GMA_TRACK mutex_acquired id=%llu",
            (unsigned long long) request_id
    );

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
        if (!g_gma_backend_initialized) {
            ggml_backend_load_all();
            LOGI("ggml_backend_load_all done first_time=1");

            int explicit_backend_loaded = 0;

            try {
                if (!native_lib_dir.empty()) {
                    for (const auto & entry :
                            std::filesystem::directory_iterator(native_lib_dir)) {

                        if (!entry.is_regular_file()) continue;

                        auto name = entry.path().filename().string();

                        if (name.rfind("libggml-cpu-", 0) == 0 &&
                            entry.path().extension() == ".so") {

                            auto full = entry.path().string();

                            LOGI(
                                "trying ggml_backend_load: %s",
                                full.c_str()
                            );

                            auto *reg = ggml_backend_load(full.c_str());

                            if (reg != nullptr) {
                                explicit_backend_loaded++;

                                LOGI(
                                    "ggml_backend_load success: %s",
                                    full.c_str()
                                );
                            } else {
                                LOGE(
                                    "ggml_backend_load returned null: %s",
                                    full.c_str()
                                );
                            }
                        }
                    }
                }
            } catch (...) {
                LOGE("filesystem scan for ggml backends failed");
            }

            LOGI(
                "explicit ggml backend loaded count=%d",
                explicit_backend_loaded
            );

            if (explicit_backend_loaded < 1) {
                LOGE("no ggml backend registered inside JNI");

                return env->NewStringUTF(
                    "GMA_LLAMA_ERROR: no_backend_loaded"
                );
            }

            llama_backend_init();
            g_gma_backend_initialized = true;

            LOGI("llama_backend_init done first_time=1");

        } else {
            LOGI("backend loading skipped already_initialized=1");
        }


        llama_model_params mparams = llama_model_default_params();
        mparams.use_mmap = true;
        mparams.use_mlock = false;
        mparams.check_tensors = false;

        llama_model *model = nullptr;

        if (g_gma_cached_model != nullptr &&
            g_gma_cached_model_path == model_path) {

            model = g_gma_cached_model;
            LOGI("GMA model cache HIT path=%s", model_path.c_str());

        } else {
            if (g_gma_cached_model != nullptr) {
                LOGI("GMA model cache path changed; freeing previous model");
                llama_model_free(g_gma_cached_model);
                g_gma_cached_model = nullptr;
                g_gma_cached_model_path.clear();
            }

            LOGI("GMA model cache MISS; loading model once");
            g_gma_cached_model =
                    llama_model_load_from_file(model_path.c_str(), mparams);

            if (!g_gma_cached_model) {
                LOGE("llama_model_load_from_file returned null");
                return env->NewStringUTF("GMA_LLAMA_ERROR: model_load_null");
            }

            g_gma_cached_model_path = model_path;
            model = g_gma_cached_model;

            LOGI("GMA model cached successfully path=%s", model_path.c_str());
        }

        llama_context_params cparams = llama_context_default_params();
        cparams.n_ctx = 1024;
        cparams.n_batch = 128;
        cparams.n_ubatch = 128;
        // Conservative Galaxy A15 CPU tuning.
        // Keep quality and generation behavior unchanged.
        cparams.n_threads = 6;
        cparams.n_threads_batch = 6;

        LOGI(
                "GMA runtime tuning threads=%d batch_threads=%d",
                cparams.n_threads,
                cparams.n_threads_batch
        );

        LOGI(
                "GMA_TRACK context_create_start id=%llu threads=%d "
                "batch_threads=%d n_ctx=%d n_batch=%d n_ubatch=%d",
                (unsigned long long) request_id,
                cparams.n_threads,
                cparams.n_threads_batch,
                cparams.n_ctx,
                cparams.n_batch,
                cparams.n_ubatch
        );

        const auto context_started_at =
                std::chrono::steady_clock::now();

        llama_context *ctx = llama_init_from_model(model, cparams);

        const double context_seconds =
                std::chrono::duration<double>(
                        std::chrono::steady_clock::now() -
                        context_started_at
                ).count();

        LOGI(
                "GMA_TRACK context_create_done id=%llu seconds=%.3f ok=%d",
                (unsigned long long) request_id,
                context_seconds,
                ctx != nullptr ? 1 : 0
        );

        if (!ctx) {
            /* Persistent GMA model: do not free per request. */
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
            tokens.resize((size_t)(-n_tokens));
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

        LOGI(
                "GMA_TRACK tokenize_done id=%llu prompt_chars=%d "
                "prompt_tokens=%d",
                (unsigned long long) request_id,
                (int) prompt.size(),
                n_tokens
        );

        if (n_tokens <= 0) {
            llama_free(ctx);
            /* Persistent GMA model: do not free per request. */
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

        LOGI(
                "GMA_TRACK prompt_decode_start id=%llu prompt_tokens=%d",
                (unsigned long long) request_id,
                n_tokens
        );

        const auto prompt_decode_started_at =
                std::chrono::steady_clock::now();

        const int prompt_decode_result =
                llama_decode(ctx, batch);

        const double prompt_decode_seconds =
                std::chrono::duration<double>(
                        std::chrono::steady_clock::now() -
                        prompt_decode_started_at
                ).count();

        LOGI(
                "GMA_TRACK prompt_decode_done id=%llu result=%d "
                "seconds=%.3f",
                (unsigned long long) request_id,
                prompt_decode_result,
                prompt_decode_seconds
        );

        if (prompt_decode_result != 0) {
            llama_batch_free(batch);
            llama_free(ctx);
            /* Persistent GMA model: do not free per request. */
            LOGE("prompt decode failed");
            return env->NewStringUTF("GMA_LLAMA_ERROR: prompt_decode_failed");
        }

        llama_sampler *sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
        llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
        llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.9f, 1));
        llama_sampler_chain_add(sampler, llama_sampler_init_dist(1234));

        std::string out;
        int pos = n_tokens;
        int generated_tokens = 0;

        const auto generation_started_at =
                std::chrono::steady_clock::now();

        int max_pred = predictLength > 0 ? predictLength : 128;
        if (max_pred > 256) max_pred = 256;

        LOGI(
                "GMA_TRACK generation_start id=%llu max_pred=%d "
                "prompt_tokens=%d",
                (unsigned long long) request_id,
                max_pred,
                n_tokens
        );

        bool ended_by_eog = false;
        bool ended_by_decode_error = false;

        for (int i = 0; i < max_pred; ++i) {
            llama_token tok = llama_sampler_sample(sampler, ctx, -1);
            llama_sampler_accept(sampler, tok);

            if (llama_vocab_is_eog(vocab, tok)) {
                ended_by_eog = true;

                LOGI(
                        "GMA_TRACK generation_eog id=%llu "
                        "generated_tokens=%d",
                        (unsigned long long) request_id,
                        generated_tokens
                );

                break;
            }

            generated_tokens++;

            if (generated_tokens == 1 ||
                generated_tokens % 16 == 0) {

                const double elapsed_seconds =
                        std::chrono::duration<double>(
                                std::chrono::steady_clock::now() -
                                generation_started_at
                        ).count();

                LOGI(
                        "GMA_TRACK generation_progress id=%llu "
                        "generated_tokens=%d seconds=%.3f "
                        "tok_per_sec=%.3f",
                        (unsigned long long) request_id,
                        generated_tokens,
                        elapsed_seconds,
                        elapsed_seconds > 0.0
                        ? generated_tokens / elapsed_seconds
                        : 0.0
                );
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
                ended_by_decode_error = true;

                LOGE(
                        "GMA_TRACK generation_decode_error id=%llu "
                        "generated_tokens=%d",
                        (unsigned long long) request_id,
                        generated_tokens
                );

                LOGE("decode failed during generation");
                break;
            }
            llama_batch_free(next);
        }

        const auto generation_finished_at =
                std::chrono::steady_clock::now();

        const double generation_seconds =
                std::chrono::duration<double>(
                        generation_finished_at - generation_started_at
                ).count();

        const double tokens_per_second =
                generation_seconds > 0.0
                ? generated_tokens / generation_seconds
                : 0.0;

        const char *stop_reason =
                ended_by_eog
                ? "eog"
                : ended_by_decode_error
                ? "decode_error"
                : generated_tokens >= max_pred
                ? "max_pred"
                : "unknown";

        LOGI(
                "GMA generation stats request_id=%llu prompt_tokens=%d "
                "generated_tokens=%d seconds=%.3f tok_per_sec=%.3f "
                "threads=%d predict=%d stop_reason=%s",
                (unsigned long long) request_id,
                n_tokens,
                generated_tokens,
                generation_seconds,
                tokens_per_second,
                cparams.n_threads,
                max_pred,
                stop_reason
        );

        LOGI(
                "GMA_TRACK request_done id=%llu reply_bytes=%d "
                "stop_reason=%s",
                (unsigned long long) request_id,
                (int) out.size(),
                stop_reason
        );

        llama_sampler_free(sampler);
        llama_batch_free(batch);
        llama_free(ctx);
        /* Persistent GMA model: do not free per request. */

        if (out.empty()) {
            return env->NewStringUTF("GMA_LLAMA_EMPTY_REPLY");
        }

        LOGI("nativeGenerate done reply_len=%d", (int) out.size());
        return env->NewStringUTF(out.c_str());

    } catch (...) {
        LOGE(
                "GMA_TRACK request_exception id=%llu",
                (unsigned long long) request_id
        );

        LOGE("nativeGenerate unknown exception");
        return env->NewStringUTF("GMA_LLAMA_ERROR: native_exception");
    }
}

extern "C"
JNIEXPORT void JNICALL
JNI_OnUnload(JavaVM *, void *) {
    std::lock_guard<std::mutex> runtime_lock(g_gma_runtime_mutex);

    if (g_gma_cached_model != nullptr) {
        LOGI("JNI_OnUnload freeing cached GMA model");
        llama_model_free(g_gma_cached_model);
        g_gma_cached_model = nullptr;
        g_gma_cached_model_path.clear();
    }

    if (g_gma_backend_initialized) {
        LOGI("JNI_OnUnload freeing llama backend");
        llama_backend_free();
        g_gma_backend_initialized = false;
    }
}

