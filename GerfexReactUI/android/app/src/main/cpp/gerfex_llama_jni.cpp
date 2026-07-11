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

// GMA system-prefix runtime cache:
// Keep one context with only the fixed system prefix decoded.
// User and generated tokens are removed after every request.
static llama_context *g_gma_prefix_ctx = nullptr;
static std::string g_gma_prefix_key;
static int32_t g_gma_prefix_tokens = 0;

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

                if (g_gma_prefix_ctx != nullptr) {
                    LOGI("GMA_TRACK prefix_context_free reason=model_changed");
                    llama_free(g_gma_prefix_ctx);
                    g_gma_prefix_ctx = nullptr;
                    g_gma_prefix_key.clear();
                    g_gma_prefix_tokens = 0;
                }

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

        const llama_vocab *vocab =
                llama_model_get_vocab(model);

        const std::string prefix_prompt =
                "<start_of_turn>user\n" +
                sys +
                "\n\n";

        const std::string suffix_prompt =
                user +
                "<end_of_turn>\n<start_of_turn>model\n";

        const std::string requested_prefix_key =
                model_path + "\n" + sys;

        auto clear_prefix_runtime = [&](const char *reason) {
            if (g_gma_prefix_ctx != nullptr) {
                LOGI(
                        "GMA_TRACK prefix_context_free id=%llu reason=%s",
                        (unsigned long long) request_id,
                        reason
                );

                llama_free(g_gma_prefix_ctx);
                g_gma_prefix_ctx = nullptr;
            }

            g_gma_prefix_key.clear();
            g_gma_prefix_tokens = 0;
        };

        auto tokenize_text = [&](
                const std::string &text,
                bool add_special,
                std::vector<llama_token> &result
        ) -> int32_t {
            result.resize(text.size() + 32);

            int32_t count = llama_tokenize(
                    vocab,
                    text.c_str(),
                    (int32_t) text.size(),
                    result.data(),
                    (int32_t) result.size(),
                    add_special,
                    true
            );

            if (count < 0) {
                result.resize((size_t) (-count));

                count = llama_tokenize(
                        vocab,
                        text.c_str(),
                        (int32_t) text.size(),
                        result.data(),
                        (int32_t) result.size(),
                        add_special,
                        true
                );
            }

            if (count > 0) {
                result.resize((size_t) count);
            }

            return count;
        };

        bool prefix_cache_hit =
                g_gma_prefix_ctx != nullptr &&
                g_gma_prefix_key == requested_prefix_key &&
                g_gma_prefix_tokens > 0;

        if (g_gma_prefix_ctx != nullptr &&
            !prefix_cache_hit) {

            LOGI(
                    "GMA_TRACK prefix_cache_reset id=%llu "
                    "reason=prefix_changed",
                    (unsigned long long) request_id
            );

            clear_prefix_runtime("prefix_changed");
        }

        if (prefix_cache_hit) {
            llama_memory_t memory =
                    llama_get_memory(g_gma_prefix_ctx);

            const bool tail_removed =
                    llama_memory_seq_rm(
                            memory,
                            0,
                            g_gma_prefix_tokens,
                            -1
                    );

            if (!tail_removed) {
                LOGI(
                        "GMA_TRACK prefix_cache_fallback id=%llu "
                        "reason=tail_remove_failed",
                        (unsigned long long) request_id
                );

                clear_prefix_runtime("tail_remove_failed");
                prefix_cache_hit = false;
            }
        }

        if (!prefix_cache_hit) {
            LOGI(
                    "GMA_TRACK prefix_cache_miss id=%llu",
                    (unsigned long long) request_id
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

            g_gma_prefix_ctx =
                    llama_init_from_model(model, cparams);

            const double context_seconds =
                    std::chrono::duration<double>(
                            std::chrono::steady_clock::now() -
                            context_started_at
                    ).count();

            LOGI(
                    "GMA_TRACK context_create_done id=%llu "
                    "seconds=%.3f ok=%d",
                    (unsigned long long) request_id,
                    context_seconds,
                    g_gma_prefix_ctx != nullptr ? 1 : 0
            );

            if (g_gma_prefix_ctx == nullptr) {
                LOGE("llama_init_from_model returned null");
                return env->NewStringUTF(
                        "GMA_LLAMA_ERROR: context_null"
                );
            }

            std::vector<llama_token> prefix_token_list;

            const int32_t prefix_count =
                    tokenize_text(
                            prefix_prompt,
                            true,
                            prefix_token_list
                    );

            LOGI(
                    "GMA_TRACK prefix_tokenize_done id=%llu "
                    "prefix_chars=%d prefix_tokens=%d",
                    (unsigned long long) request_id,
                    (int) prefix_prompt.size(),
                    prefix_count
            );

            if (prefix_count <= 0) {
                clear_prefix_runtime("prefix_tokenize_failed");

                return env->NewStringUTF(
                        "GMA_LLAMA_ERROR: tokenize_failed"
                );
            }

            llama_batch prefix_batch =
                    llama_batch_init(prefix_count, 0, 1);

            for (int i = 0; i < prefix_count; ++i) {
                prefix_batch.token[i] = prefix_token_list[i];
                prefix_batch.pos[i] = i;
                prefix_batch.n_seq_id[i] = 1;
                prefix_batch.seq_id[i][0] = 0;
                prefix_batch.logits[i] = false;
            }

            prefix_batch.n_tokens = prefix_count;

            LOGI(
                    "GMA_TRACK prefix_decode_start id=%llu "
                    "prefix_tokens=%d",
                    (unsigned long long) request_id,
                    prefix_count
            );

            const auto prefix_decode_started_at =
                    std::chrono::steady_clock::now();

            const int prefix_decode_result =
                    llama_decode(
                            g_gma_prefix_ctx,
                            prefix_batch
                    );

            const double prefix_decode_seconds =
                    std::chrono::duration<double>(
                            std::chrono::steady_clock::now() -
                            prefix_decode_started_at
                    ).count();

            llama_batch_free(prefix_batch);

            LOGI(
                    "GMA_TRACK prefix_decode_done id=%llu "
                    "result=%d seconds=%.3f",
                    (unsigned long long) request_id,
                    prefix_decode_result,
                    prefix_decode_seconds
            );

            if (prefix_decode_result != 0) {
                clear_prefix_runtime("prefix_decode_failed");

                return env->NewStringUTF(
                        "GMA_LLAMA_ERROR: prompt_decode_failed"
                );
            }

            g_gma_prefix_key = requested_prefix_key;
            g_gma_prefix_tokens = prefix_count;

            LOGI(
                    "GMA_TRACK prefix_cache_stored id=%llu "
                    "prefix_tokens=%d",
                    (unsigned long long) request_id,
                    g_gma_prefix_tokens
            );

        } else {
            LOGI(
                    "GMA_TRACK prefix_cache_hit id=%llu "
                    "prefix_tokens=%d",
                    (unsigned long long) request_id,
                    g_gma_prefix_tokens
            );
        }

        llama_context *ctx = g_gma_prefix_ctx;

        std::vector<llama_token> suffix_tokens;

        const int32_t suffix_count =
                tokenize_text(
                        suffix_prompt,
                        false,
                        suffix_tokens
                );

        const int32_t n_tokens =
                g_gma_prefix_tokens + suffix_count;

        LOGI(
                "GMA_TRACK tokenize_done id=%llu "
                "prefix_tokens=%d suffix_tokens=%d total_tokens=%d "
                "prompt_chars=%d",
                (unsigned long long) request_id,
                g_gma_prefix_tokens,
                suffix_count,
                n_tokens,
                (int) (
                        prefix_prompt.size() +
                        suffix_prompt.size()
                )
        );

        if (suffix_count <= 0) {
            clear_prefix_runtime("suffix_tokenize_failed");

            return env->NewStringUTF(
                    "GMA_LLAMA_ERROR: tokenize_failed"
            );
        }

        llama_batch batch =
                llama_batch_init(suffix_count, 0, 1);

        for (int i = 0; i < suffix_count; ++i) {
            batch.token[i] = suffix_tokens[i];
            batch.pos[i] = g_gma_prefix_tokens + i;
            batch.n_seq_id[i] = 1;
            batch.seq_id[i][0] = 0;
            batch.logits[i] = (i == suffix_count - 1);
        }

        batch.n_tokens = suffix_count;

        LOGI(
                "GMA_TRACK prompt_decode_start id=%llu "
                "prefix_cache_hit=%d suffix_tokens=%d total_tokens=%d",
                (unsigned long long) request_id,
                prefix_cache_hit ? 1 : 0,
                suffix_count,
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
                "seconds=%.3f prefix_cache_hit=%d",
                (unsigned long long) request_id,
                prompt_decode_result,
                prompt_decode_seconds,
                prefix_cache_hit ? 1 : 0
        );

        if (prompt_decode_result != 0) {
            llama_batch_free(batch);
            clear_prefix_runtime("suffix_decode_failed");

            LOGE("prompt decode failed");

            return env->NewStringUTF(
                    "GMA_LLAMA_ERROR: prompt_decode_failed"
            );
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

        // One limited continuation only when GMA does not reach EOG.
        // Main: 64 -> 96. Learning: 128 -> 192.
        const int extension_tokens =
                max_pred <= 64 ? 32 : 64;

        const int hard_max_pred =
                std::min(256, max_pred + extension_tokens);

        bool extension_activated = false;

        LOGI(
                "GMA_TRACK generation_start id=%llu max_pred=%d "
                "hard_max_pred=%d prompt_tokens=%d",
                (unsigned long long) request_id,
                max_pred,
                hard_max_pred,
                n_tokens
        );

        bool ended_by_eog = false;
        bool ended_by_decode_error = false;

        for (int i = 0; i < hard_max_pred; ++i) {
            if (!extension_activated && i == max_pred) {
                extension_activated = true;

                LOGI(
                        "GMA_TRACK generation_extension id=%llu "
                        "from=%d to=%d",
                        (unsigned long long) request_id,
                        max_pred,
                        hard_max_pred
                );
            }
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
                : generated_tokens >= hard_max_pred
                ? "extended_max_pred"
                : extension_activated
                ? "extension_incomplete"
                : "unknown";

        LOGI(
                "GMA generation stats request_id=%llu prompt_tokens=%d "
                "generated_tokens=%d seconds=%.3f tok_per_sec=%.3f "
                "threads=%d predict=%d hard_predict=%d "
                "extended=%d stop_reason=%s",
                (unsigned long long) request_id,
                n_tokens,
                generated_tokens,
                generation_seconds,
                tokens_per_second,
                cparams.n_threads,
                max_pred,
                hard_max_pred,
                extension_activated ? 1 : 0,
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

        const bool prefix_tail_removed =
                llama_memory_seq_rm(
                        llama_get_memory(ctx),
                        0,
                        g_gma_prefix_tokens,
                        -1
                );

        LOGI(
                "GMA_TRACK prefix_tail_reset id=%llu ok=%d "
                "prefix_tokens=%d",
                (unsigned long long) request_id,
                prefix_tail_removed ? 1 : 0,
                g_gma_prefix_tokens
        );

        if (!prefix_tail_removed) {
            clear_prefix_runtime("request_end_tail_remove_failed");
        }

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

    if (g_gma_prefix_ctx != nullptr) {
        LOGI("JNI_OnUnload freeing GMA prefix context");
        llama_free(g_gma_prefix_ctx);
        g_gma_prefix_ctx = nullptr;
        g_gma_prefix_key.clear();
        g_gma_prefix_tokens = 0;
    }

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

