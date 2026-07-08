#include <jni.h>
#include <string>
#include <algorithm>
#include <sys/stat.h>
#include <cstdio>
#include <cerrno>
#include <vector>
#include <sstream>
#include <android/log.h>
#include <dlfcn.h>

#include "llama.h"
#include "ggml-backend.h"

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "GMA_LLAMA", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "GMA_LLAMA", __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, "GMA_LLAMA", __VA_ARGS__)

static std::string jstr(JNIEnv *env, jstring s) {
    if (!s) return "";
    const char *c = env->GetStringUTFChars(s, nullptr);
    std::string out = c ? c : "";
    if (c) env->ReleaseStringUTFChars(s, c);
    return out;
}

#define GMA_STR_HELPER(x) #x
#define GMA_STR(x) GMA_STR_HELPER(x)

#ifdef LLAMA_BUILD_NUMBER
static const char *GMA_LLAMA_BUILD = GMA_STR(LLAMA_BUILD_NUMBER);
#else
static const char *GMA_LLAMA_BUILD = "unknown";
#endif

static std::string g_gma_llama_log;

static void gma_llama_log_cb(enum ggml_log_level level, const char * text, void * user_data) {
    if (!text) return;

    if (g_gma_llama_log.size() < 32000) {
        g_gma_llama_log += text;
    }

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
}

static std::string gma_trim_log(std::string s, size_t max_len = 4000) {
    std::replace(s.begin(), s.end(), '\n', ' ');
    std::replace(s.begin(), s.end(), '\r', ' ');
    if (s.size() > max_len) {
        s = s.substr(s.size() - max_len);
    }
    return s;
}

static std::string gma_file_debug(const std::string &model_path) {
    struct stat st{};
    errno = 0;
    int stat_rc = stat(model_path.c_str(), &st);
    int stat_errno = errno;

    unsigned char head[16] = {0};
    errno = 0;
    FILE *fp = fopen(model_path.c_str(), "rb");
    int fopen_errno = errno;
    long head_n = -1;
    if (fp) {
        head_n = (long) fread(head, 1, 16, fp);
        fclose(fp);
    }

    char buf[1024];
    snprintf(
        buf, sizeof(buf),
        "stat_rc=%d | stat_errno=%d | stat_size=%lld | fopen=%s | fopen_errno=%d | head_n=%ld | head=%02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x",
        stat_rc,
        stat_errno,
        (long long)(stat_rc == 0 ? st.st_size : -1),
        fp ? "ok" : "fail",
        fopen_errno,
        head_n,
        head[0], head[1], head[2], head[3], head[4], head[5], head[6], head[7],
        head[8], head[9], head[10], head[11], head[12], head[13], head[14], head[15]
    );
    return std::string(buf);
}


static std::vector<ggml_backend_reg_t> g_gma_backend_regs;
static bool g_gma_manual_backends_loaded = false;

static int gma_manual_load_cpu_backends(const std::string &native_lib_dir, std::string &report) {
    const char *names[] = {
        "libggml-cpu-android_armv8.0_1.so",
        "libggml-cpu-android_armv8.2_1.so",
        "libggml-cpu-android_armv8.2_2.so",
        "libggml-cpu-android_armv8.6_1.so",
        "libggml-cpu-android_armv9.0_1.so",
        "libggml-cpu-android_armv9.2_1.so",
        "libggml-cpu-android_armv9.2_2.so",
    };

    if (g_gma_manual_backends_loaded && !g_gma_backend_regs.empty()) {
        report += "manual_backends_already_loaded=" + std::to_string((int)g_gma_backend_regs.size()) + "; ";
        return (int)g_gma_backend_regs.size();
    }

    int loaded = 0;

    for (const char *name : names) {
        std::string path = native_lib_dir;
        if (!path.empty() && path.back() != '/') path += "/";
        path += name;

        struct stat st{};
        int stat_rc = stat(path.c_str(), &st);

        report += std::string(name) + "[";
        report += "stat=" + std::to_string(stat_rc);
        if (stat_rc == 0) report += ",size=" + std::to_string((long long)st.st_size);

        ggml_backend_reg_t reg = ggml_backend_load(path.c_str());
        if (reg) {
            g_gma_backend_regs.push_back(reg);
            loaded++;
            report += ",ggml_backend_load=OK";
            LOGI("manual backend loaded: %s", path.c_str());
        } else {
            const char *err = dlerror();
            report += ",ggml_backend_load=FAIL";
            if (err) {
                report += ",dlerror=";
                report += err;
            }
            LOGE("manual backend failed: %s", path.c_str());
        }

        report += "]; ";
    }

    if (loaded > 0) {
        g_gma_manual_backends_loaded = true;
    }

    return loaded;
}

static std::string gma_model_load_error_debug(
        const std::string &model_path,
        const std::string &native_lib_dir,
        const llama_model_params &mparams) {

    std::string log = gma_trim_log(g_gma_llama_log, 5000);
    std::string fdbg = gma_file_debug(model_path);

    char buf[8192];
    snprintf(
        buf,
        sizeof(buf),
        "GMA_LLAMA_ERROR: model_load_null | llama_build=%s | model_path=%s | nativeLibDir=%s | use_mmap=%d | use_mlock=%d | check_tensors=%d | %s | llama_log=%s",
        GMA_LLAMA_BUILD,
        model_path.c_str(),
        native_lib_dir.c_str(),
        (int)mparams.use_mmap,
        (int)mparams.use_mlock,
        (int)mparams.check_tensors,
        fdbg.c_str(),
        log.c_str()
    );
    return std::string(buf);
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
    LOGI("nativeLibDir=%s", native_lib_dir.c_str());

    try {
        g_gma_llama_log.clear();

        // callback واحد فقط — لا نعيد استبداله
        llama_log_set(gma_llama_log_cb, nullptr);

        std::string backend_report;
        int manual_backend_count = gma_manual_load_cpu_backends(native_lib_dir, backend_report);
        LOGI("manual_backend_count=%d report=%s", manual_backend_count, backend_report.c_str());

        LOGI("calling ggml_backend_load_all()");
        ggml_backend_load_all();
        LOGI("ggml_backend_load_all done; llama_build=%s", GMA_LLAMA_BUILD);

        if (manual_backend_count <= 0) {
            std::string err = "GMA_LLAMA_ERROR: backend_load_failed | nativeLibDir=" + native_lib_dir
                    + " | backend_report=" + backend_report
                    + " | llama_log=" + gma_trim_log(g_gma_llama_log, 3000);
            LOGE("%s", err.c_str());
            return env->NewStringUTF(err.c_str());
        }

        LOGI("calling llama_backend_init()");
        llama_backend_init();
        LOGI("llama_backend_init done");

        llama_model_params mparams = llama_model_default_params();
        mparams.use_mmap = true;
        mparams.use_mlock = false;
        mparams.check_tensors = false;

        LOGI("llama_model_load_from_file begin: mmap=%d mlock=%d check_tensors=%d",
             (int)mparams.use_mmap,
             (int)mparams.use_mlock,
             (int)mparams.check_tensors);

        llama_model *model = llama_model_load_from_file(model_path.c_str(), mparams);
        if (!model) {
            std::string dbg = gma_model_load_error_debug(model_path, native_lib_dir, mparams);
            LOGE("%s", dbg.c_str());
            llama_backend_free();
            return env->NewStringUTF(dbg.c_str());
        }

        LOGI("model load OK");

        llama_context_params cparams = llama_context_default_params();
        cparams.n_ctx = 512;
        cparams.n_batch = 32;
        cparams.n_ubatch = 32;
        cparams.n_threads = 4;
        cparams.n_threads_batch = 4;

        llama_context *ctx = llama_init_from_model(model, cparams);
        if (!ctx) {
            llama_model_free(model);
            llama_backend_free();
            LOGE("GMA_LLAMA_ERROR: context_null");
            return env->NewStringUTF("GMA_LLAMA_ERROR: context_null");
        }

        const llama_vocab *vocab = llama_model_get_vocab(model);

        std::string prompt =
                "<start_of_turn>user\n" +
                sys + "\n\n" +
                user +
                "<end_of_turn>\n<start_of_turn>model\n";

        std::vector<llama_token> tokens(prompt.size() + 64);
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

        if (n_tokens <= 0) {
            llama_free(ctx);
            llama_model_free(model);
            llama_backend_free();
            LOGE("GMA_LLAMA_ERROR: tokenize_failed n=%d", n_tokens);
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

        LOGI("prompt decode inputs: n_tokens=%d n_batch=%u n_ctx=%u",
             n_tokens,
             cparams.n_batch,
             cparams.n_ctx);

        int decode_ret = llama_decode(ctx, batch);
        LOGI("llama_decode returned: %d", decode_ret);

        if (decode_ret != 0) {
            std::string err =
                    "GMA_LLAMA_ERROR: prompt_decode_failed"
                    " | decode_ret=" + std::to_string(decode_ret) +
                    " | n_tokens=" + std::to_string(n_tokens) +
                    " | n_batch=" + std::to_string((unsigned)cparams.n_batch) +
                    " | n_ctx=" + std::to_string((unsigned)cparams.n_ctx);
            LOGE("%s", err.c_str());
            llama_batch_free(batch);
            llama_free(ctx);
            llama_model_free(model);
            llama_backend_free();
            return env->NewStringUTF(err.c_str());
        }

        llama_sampler *sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
        llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
        llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.9f, 1));
        llama_sampler_chain_add(sampler, llama_sampler_init_dist(1234));

        std::string out;
        int pos = n_tokens;
        int max_pred = predictLength > 0 ? predictLength : 64;
        if (max_pred > 64) max_pred = 64;

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
                break;
            }
            llama_batch_free(next);
        }

        llama_sampler_free(sampler);
        llama_batch_free(batch);
        llama_free(ctx);
        llama_model_free(model);
        llama_backend_free();

        if (out.empty()) {
            return env->NewStringUTF("GMA_LLAMA_ERROR: empty_reply");
        }

        return env->NewStringUTF(out.c_str());

    } catch (const std::exception &e) {
        std::string err = std::string("GMA_LLAMA_ERROR: exception: ") + e.what();
        LOGE("%s", err.c_str());
        llama_backend_free();
        return env->NewStringUTF(err.c_str());
    } catch (...) {
        LOGE("GMA_LLAMA_ERROR: unknown_exception");
        llama_backend_free();
        return env->NewStringUTF("GMA_LLAMA_ERROR: unknown_exception");
    }
}
