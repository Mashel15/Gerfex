package com.mashel15.gerfex;

import android.content.Intent;
import com.getcapacitor.annotation.ActivityCallback;
import androidx.activity.result.ActivityResult;
import android.speech.RecognizerIntent;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.JSObject;
import com.getcapacitor.annotation.CapacitorPlugin;

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.TimeZone;
import java.net.URL;
import java.net.HttpURLConnection;

@CapacitorPlugin(name = "Gerfex")
public class GerfexPlugin extends Plugin {
private String mapPackage(String name) {
        if (name == null) return "";
        String p = name.toLowerCase();
        if (p.equals("chrome")) return "com.android.chrome";
        if (p.equals("youtube")) return "com.google.android.youtube";
        if (p.equals("settings")) return "android.settings";
        return p;
    }

    private boolean openApp(String pkg) {
        try {
            String mapped = mapPackage(pkg);

            if ("android.settings".equals(mapped)) {
                Intent intent = new Intent(android.provider.Settings.ACTION_SETTINGS);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                return true;
            }

            PackageManager pm = getContext().getPackageManager();
            Intent intent = pm.getLaunchIntentForPackage(mapped);

            if (intent == null && "com.android.chrome".equals(mapped)) {
                intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com"));
            }

            if (intent == null && "com.google.android.youtube".equals(mapped)) {
                intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com"));
            }

            if (intent == null) return false;

            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean openUrl(String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean executeAction(JSONObject action) {
        try {
            if (action == null) return false;

            String name = action.optString("action", "");
            JSONObject args = action.optJSONObject("args");
            if (args == null) args = new JSONObject();

            if ("open_app".equals(name)) {
                return openApp(args.optString("package", ""));
            }

            if ("open_url".equals(name)) {
                return openUrl(args.optString("url", ""));
            }

            if ("press_home".equals(name)) {
                if (GerfexAccessibilityService.isReady()) {
                    return GerfexAccessibilityService.pressHome();
                }
                Intent intent = new Intent(Intent.ACTION_MAIN);
                intent.addCategory(Intent.CATEGORY_HOME);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                return true;
            }

            if ("press_back".equals(name)) {
                return GerfexAccessibilityService.pressBack();
            }

            if ("tap".equals(name)) {
                return GerfexAccessibilityService.tap(
                    (float) args.optDouble("x", 0),
                    (float) args.optDouble("y", 0)
                );
            }

            if ("swipe".equals(name)) {
                return GerfexAccessibilityService.swipe(
                    (float) args.optDouble("x1", 0),
                    (float) args.optDouble("y1", 0),
                    (float) args.optDouble("x2", 0),
                    (float) args.optDouble("y2", 0),
                    args.optLong("duration", 400)
                );
            }

            if ("wait".equals(name)) {
                try { Thread.sleep(args.optInt("seconds", 1) * 1000L); } catch(Exception ignored) {}
                return true;
            }

            if ("dump_ui".equals(name) || "observe_screen".equals(name)) {
                String screenText = GerfexAccessibilityService.dumpText();
                saveNativeScreenText(screenText);
                return GerfexAccessibilityService.isReady();
            }

            return false;

        } catch (Exception e) {
            return false;
        }
    }


    private String isoNow() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
        return sdf.format(new Date());
    }

    private File executionTraceFile() {
        File traceDir = new File(getContext().getFilesDir(), "gerfex_runtime_data/development/trace");
        traceDir.mkdirs();
        return new File(traceDir, "execution_trace.jsonl");
    }

    private File executionPathFile() {
        File traceDir = new File(getContext().getFilesDir(), "gerfex_runtime_data/development/trace");
        traceDir.mkdirs();
        return new File(traceDir, "execution_path.jsonl");
    }

    private void appendPluginTrace(String traceId, JSONObject action, String stageName, boolean ok) {
        try {
            if (traceId == null || traceId.length() == 0) return;

            File file = executionTraceFile();
            if (!file.exists()) return;

            List<String> lines = new ArrayList<>();
            BufferedReader br = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)
            );

            String line;
            while ((line = br.readLine()) != null) {
                if (line.trim().length() > 0) lines.add(line);
            }
            br.close();

            List<String> out = new ArrayList<>();

            for (String rawLine : lines) {
                JSONObject obj = new JSONObject(rawLine);

                if (traceId.equals(obj.optString("trace_id", ""))) {
                    JSONArray stages = obj.optJSONArray("stages");
                    if (stages == null) stages = new JSONArray();

                    JSONObject stage = new JSONObject();
                    stage.put("time", isoNow());
                    stage.put("stage", stageName);
                    stage.put("source", "GerfexPlugin");

                    if (action != null) {
                        stage.put("action", action.optString("action", ""));
                        JSONObject args = action.optJSONObject("args");
                        if (args != null) stage.put("args", args);
                    }

                    if ("plugin_execute_end".equals(stageName)) {
                        stage.put("ok", ok);
                    }

                    stages.put(stage);
                    obj.put("stages", stages);
                }

                out.add(obj.toString());
            }

            FileOutputStream fos = new FileOutputStream(file, false);
            fos.write((String.join("\n", out) + "\n").getBytes(StandardCharsets.UTF_8));
            fos.close();

        } catch (Exception ignored) {}
    }

    private int executeFromResult(String result) {
        int count = 0;
        try {
            JSONObject root = new JSONObject(result);
            String traceId = root.optString("trace_id", "");
            JSONObject raw = root.optJSONObject("raw");
            if (raw == null) return 0;

            JSONObject execution = raw.optJSONObject("execution");
            if (execution == null) return 0;

            JSONArray nativeActions = execution.optJSONArray("native_actions");
            if (nativeActions != null) {
                for (int i = 0; i < nativeActions.length(); i++) {
                    JSONObject a = nativeActions.optJSONObject(i);
                    if (a != null) {
                        appendPluginTrace(traceId, a, "plugin_execute_start", true);
                        boolean executed = executeAction(a);
                        appendPluginTrace(traceId, a, "plugin_execute_end", executed);
                        if (executed) count++;
                    }
                }
                return count;
            }

            JSONObject decision = execution.optJSONObject("decision");
            if (decision == null) decision = raw.optJSONObject("decision");
            if (decision == null) return 0;

            JSONArray actions = decision.optJSONArray("actions");
            if (actions != null) {
                for (int i = 0; i < actions.length(); i++) {
                    JSONObject a = actions.optJSONObject(i);
                    if (a != null) {
                        appendPluginTrace(traceId, a, "plugin_execute_start", true);
                        boolean executed = executeAction(a);
                        appendPluginTrace(traceId, a, "plugin_execute_end", executed);
                        if (executed) count++;
                    }
                }
                return count;
            }

            JSONObject action = decision.optJSONObject("action");
            if (action != null) {
                appendPluginTrace(traceId, action, "plugin_execute_start", true);
                boolean executed = executeAction(action);
                appendPluginTrace(traceId, action, "plugin_execute_end", executed);
                if (executed) count++;
            }

        } catch (Exception ignored) {}

        return count;
    }

    private String saveNativeScreenText(String text) {
        try {
            File runtimeDir = new File(getContext().getFilesDir(), "gerfex_runtime_data/runtime");
            runtimeDir.mkdirs();

            File out = new File(runtimeDir, "native_screen_text.txt");
            FileOutputStream fos = new FileOutputStream(out, false);
            fos.write((text == null ? "" : text).getBytes(StandardCharsets.UTF_8));
            fos.close();

            return out.getAbsolutePath();
        } catch (Exception e) {
            return "";
        }
    }


    @PluginMethod
    public void readExecutionTrace(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            File file = executionTraceFile();
            if (!file.exists()) {
                ret.put("ok", true);
                ret.put("content", "");
                call.resolve(ret);
                return;
            }

            BufferedReader br = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)
            );

            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
            br.close();

            ret.put("ok", true);
            ret.put("content", sb.toString());
            ret.put("path", file.getAbsolutePath());
            call.resolve(ret);
        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }

    @PluginMethod
    public void readExecutionPath(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            File file = executionPathFile();
            if (!file.exists()) {
                ret.put("ok", true);
                ret.put("content", "");
                call.resolve(ret);
                return;
            }

            BufferedReader br = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)
            );

            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
            br.close();

            ret.put("ok", true);
            ret.put("content", sb.toString());
            ret.put("path", file.getAbsolutePath());
            call.resolve(ret);
        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }

    @PluginMethod
    public void accessibilityStatus(PluginCall call) {
        JSObject ret = new JSObject();
        String screenText = GerfexAccessibilityService.dumpText();
        String savedPath = saveNativeScreenText(screenText);

        ret.put("ok", true);
        ret.put("ready", GerfexAccessibilityService.isReady());
        ret.put("screen_text", screenText);
        ret.put("screen_text_saved_path", savedPath);
        call.resolve(ret);
    }




    private void appendGmaJavaTrace(String stage, String detail) {
        try {
            Log.i("GERFEX_GMA_TRACE", stage + " | " + detail);

            File dir = new File(getContext().getFilesDir(), "gerfex_runtime_data/runtime");
            if (!dir.exists()) dir.mkdirs();

            File file = new File(dir, "gma_java_trace.txt");
            FileWriter writer = new FileWriter(file, true);
            writer.write(System.currentTimeMillis() + " | " + stage + " | " + detail + "\n");
            writer.close();
        } catch (Throwable ignored) {}
    }

    @PluginMethod
    public void getGmaTrace(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            File dir = new File(getContext().getFilesDir(), "gerfex_runtime_data/runtime");
            File file = new File(dir, "gma_java_trace.txt");
            String content = "";
            if (file.exists()) {
                byte[] bytes = java.nio.file.Files.readAllBytes(file.toPath());
                content = new String(bytes, java.nio.charset.StandardCharsets.UTF_8);
                if (content.length() > 20000) {
                    content = content.substring(content.length() - 20000);
                }
            }
            ret.put("ok", true);
            ret.put("path", file.getAbsolutePath());
            ret.put("exists", file.exists());
            ret.put("content", content);
            call.resolve(ret);
        } catch (Throwable e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }

    private String limitGmaPrompt(String prompt, String mode) {
        if (prompt == null) return "";
        int maxChars = "learning".equals(mode) ? 1400 : 1800;
        if (prompt.length() <= maxChars) return prompt;

        String kept = prompt.substring(prompt.length() - maxChars);
        return "[GMA_PROMPT_TRIMMED original_chars=" + prompt.length()
                + " kept_chars=" + kept.length()
                + " mode=" + mode + "]\n" + kept;
    }

    private String fillGmaNativeIfNeeded(String result, String speakerName) {
        long t0 = System.currentTimeMillis();
        try {
            appendGmaJavaTrace("fill_native_enter", "result_len=" + (result == null ? 0 : result.length()));
            JSONObject root = new JSONObject(result);

            if (!root.optBoolean("needs_gma_native", false)) {
                appendGmaJavaTrace("fill_native_skip_no_need", "elapsed_ms=" + (System.currentTimeMillis() - t0));
                return result;
            }

            String traceId = root.optString("trace_id", "");
            String prompt = root.optString("gma_prompt", root.optString("reply", ""));
            String mode = root.optString("gma_mode", "main");
            int originalPromptLen = prompt.length();
            prompt = limitGmaPrompt(prompt, mode);
            appendGmaJavaTrace("fill_native_prompt_budget", "mode=" + mode + " original_len=" + originalPromptLen + " final_len=" + prompt.length());

            JSONObject requestStage = new JSONObject();
            requestStage.put("action", "gma_native_surface");
            requestStage.put("args", new JSONObject().put("mode", mode).put("speaker", speakerName));
            appendPluginTrace(traceId, requestStage, "surface_native_requested", true);

            File model = ensureGmaModelFile();
            appendGmaJavaTrace("fill_native_model_ready", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " model_size=" + model.length() + " canRead=" + model.canRead());

            JSONObject startStage = new JSONObject();
            startStage.put("action", "gma_native_bridge");
            startStage.put("args", new JSONObject().put("mode", mode).put("model_size", model.length()));
            appendPluginTrace(traceId, startStage, "surface_native_bridge_start", true);

            String modelDebug = " path=" + model.getAbsolutePath()
                + " exists=" + model.exists()
                + " canRead=" + model.canRead()
                + " length=" + model.length();

            appendGmaJavaTrace("fill_native_generate_start", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " prompt_len=" + prompt.length() + " bridge_stage=" + GmaLlamaBridge.getLastStage());
            String nativeReply = GmaLlamaBridge.generateBlocking(getContext(), model.getAbsolutePath(), prompt, 256);
            String replyText = nativeReply == null ? "" : nativeReply.trim();
            appendGmaJavaTrace("fill_native_generate_done", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " reply_len=" + replyText.length() + " bridge_stage=" + GmaLlamaBridge.getLastStage());

            String errorCode = null;
            if (replyText.length() == 0) {
                errorCode = "GMA_LLAMA_EMPTY_REPLY";
            } else if (replyText.contains("GMA_LLAMA_ERROR")) {
                errorCode = replyText;
            } else if (replyText.contains("GMA_LLAMA_EMPTY_REPLY")) {
                errorCode = "GMA_LLAMA_EMPTY_REPLY";
            } else if (replyText.contains("model_load_null")) {
                errorCode = "model_load_null";
            } else if (replyText.contains("context_null")) {
                errorCode = "context_null";
            } else if (replyText.contains("no_backend_loaded")) {
                errorCode = "no_backend_loaded";
            } else if (replyText.contains("prompt_decode_failed")) {
                errorCode = "prompt_decode_failed";
            } else if (replyText.contains("generation_decode_failed")) {
                errorCode = "generation_decode_failed";
            } else if (replyText.contains("generation_timeout")) {
                errorCode = "generation_timeout";
            } else if (replyText.contains("generation_no_tokens")) {
                errorCode = "generation_no_tokens";
            } else if (replyText.contains("tokenize_failed")) {
                errorCode = "tokenize_failed";
            } else if (replyText.contains("native_exception")) {
                errorCode = "native_exception";
            }

            root.put("speaker", speakerName);
            root.put("surface_native_gma_used", true);
            root.put("gma_mode", mode);
            root.put("bridge_stage", GmaLlamaBridge.getLastStage());
            root.put("model_path", model.getAbsolutePath());
            root.put("model_size", model.length());

            if (errorCode != null) {
                root.put("ok", false);
                root.put("stage", "surface_native_reply_error");
                root.put("error_code", errorCode);
                root.put("error", replyText);
                root.put("reply", "خطأ في GMA Native: " + errorCode + " | modelDebug:" + modelDebug);

                JSONObject errorStage = new JSONObject();
                errorStage.put("action", "gma_native_reply");
                errorStage.put("args", new JSONObject()
                    .put("mode", mode)
                    .put("error_code", errorCode)
                    .put("bridge_stage", GmaLlamaBridge.getLastStage()));
                appendPluginTrace(traceId, errorStage, "surface_native_reply_error", false);
                appendGmaJavaTrace("fill_native_error_reply", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " error_code=" + errorCode + " bridge_stage=" + GmaLlamaBridge.getLastStage());
            } else {
                root.put("ok", true);
                root.put("stage", "surface_native_done");
                root.put("reply", nativeReply);

                JSONObject doneStage = new JSONObject();
                doneStage.put("action", "gma_native_reply");
                doneStage.put("args", new JSONObject()
                    .put("mode", mode)
                    .put("reply_len", replyText.length())
                    .put("bridge_stage", GmaLlamaBridge.getLastStage()));
                appendPluginTrace(traceId, doneStage, "surface_native_done", true);
                appendGmaJavaTrace("fill_native_done", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " reply_len=" + replyText.length() + " bridge_stage=" + GmaLlamaBridge.getLastStage());
            }

            return root.toString();

        } catch (Throwable e) {
            appendGmaJavaTrace("fill_native_exception", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " error=" + e.toString() + " bridge_stage=" + GmaLlamaBridge.getLastStage());
            try {
                JSONObject err = new JSONObject(result);
                err.put("ok", false);
                err.put("speaker", speakerName);
                err.put("stage", "surface_native_exception");
                err.put("error", e.toString());
                err.put("reply", "خطأ داخلي في ربط GMA Native: " + e.toString());
                return err.toString();
            } catch (Exception ignored) {
                return result;
            }
        }
    }

    @PluginMethod
    public void thinkMain(PluginCall call) {
        String message = call.getString("message", "");
        JSObject modelStateObj = call.getObject("model_state", new JSObject());
        String modelStateJson = modelStateObj.toString();

        new Thread(() -> {
            long t0 = System.currentTimeMillis();
            JSObject ret = new JSObject();
            try {
                appendGmaJavaTrace("think_main_enter", "msg_len=" + message.length());

                appendGmaJavaTrace("think_main_python_start", "elapsed_ms=" + (System.currentTimeMillis() - t0));
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getContext()));
                }

                Python py = Python.getInstance();
                PyObject entry = py.getModule("gerfex_entry");
                String result = entry.callAttr("think_main", message, modelStateJson).toString();
                appendGmaJavaTrace("think_main_python_done", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " result_len=" + result.length());

                appendGmaJavaTrace("think_main_fill_native_start", "elapsed_ms=" + (System.currentTimeMillis() - t0));
                result = fillGmaNativeIfNeeded(result, "Gerfex");
                appendGmaJavaTrace("think_main_fill_native_done", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " result_len=" + result.length());

                appendGmaJavaTrace("think_main_execute_result_start", "elapsed_ms=" + (System.currentTimeMillis() - t0));
                int nativeCount = executeFromResult(result);
                appendGmaJavaTrace("think_main_execute_result_done", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " native_count=" + nativeCount);

                ret.put("ok", true);
                ret.put("result", result);
                ret.put("native_executed_count", nativeCount);
                appendGmaJavaTrace("think_main_resolve_ok", "elapsed_ms=" + (System.currentTimeMillis() - t0));
                call.resolve(ret);
            } catch (Throwable e) {
                appendGmaJavaTrace("think_main_exception", "elapsed_ms=" + (System.currentTimeMillis() - t0) + " error=" + e.toString());
                ret.put("ok", false);
                ret.put("error", e.toString());
                call.resolve(ret);
            }
        }, "gerfex-think-main").start();
    }

    @PluginMethod
    public void thinkLearning(PluginCall call) {
        String message = call.getString("message", "");
        JSObject learningStateObj = call.getObject("learning_state", new JSObject());
        String learningStateJson = learningStateObj.toString();

        new Thread(() -> {
            JSObject ret = new JSObject();
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getContext()));
                }

                Python py = Python.getInstance();
                PyObject entry = py.getModule("gerfex_entry");
                String result = entry.callAttr("think_learning", message, learningStateJson).toString();
                result = fillGmaNativeIfNeeded(result, "GMA");

                ret.put("ok", true);
                ret.put("result", result);
                ret.put("native_executed_count", 0);
                call.resolve(ret);
            } catch (Exception e) {
                ret.put("ok", false);
                ret.put("error", e.toString());
                call.resolve(ret);
            }
        }).start();
    }

    @PluginMethod
    public void think(PluginCall call) {
        String message = call.getString("message", "");
        JSObject modelStateObj = call.getObject("model_state", new JSObject());
        String modelStateJson = modelStateObj.toString();

        new Thread(() -> {
            JSObject ret = new JSObject();

            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getContext()));
                }

                String screenTextBeforeThink = GerfexAccessibilityService.dumpText();
                String screenTextPath = saveNativeScreenText(screenTextBeforeThink);

                Python py = Python.getInstance();
                PyObject entry = py.getModule("gerfex_entry");
                String result = entry.callAttr("think", message, modelStateJson).toString();

                int nativeCount = executeFromResult(result);

                try { Thread.sleep(1500L); } catch(Exception ignored) {}

                String screenTextAfterExecution = GerfexAccessibilityService.dumpText();
                String screenTextAfterPath = saveNativeScreenText(screenTextAfterExecution);

                boolean screenReadyAfterExecution = GerfexAccessibilityService.isReady();
                int screenTextAfterLength = screenTextAfterExecution == null ? 0 : screenTextAfterExecution.length();

                JSObject verification = new JSObject();
                verification.put("ok", screenReadyAfterExecution);
                verification.put("native_executed_count", nativeCount);
                verification.put("screen_text_length", screenTextAfterLength);
                verification.put("screen_text_saved_path", screenTextAfterPath);
                verification.put("note", "Verified Execution Loop V1: post-execution screen captured only.");

                ret.put("ok", true);
                ret.put("result", result);
                ret.put("native_executed_count", nativeCount);
                ret.put("screen_text_saved_path", screenTextPath);
                ret.put("post_execution_verification", verification);

                call.resolve(ret);

            } catch (Exception e) {
                ret.put("ok", false);
                ret.put("error", e.toString());
                call.resolve(ret);
            }
        }).start();
    }


    @PluginMethod
    public void saveExternalModels(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            String registryJson = call.getString("registry", "{\"version\":\"EXTERNAL_MODELS_REGISTRY_V1\",\"mode\":\"advisor_only\",\"active\":[],\"providers\":[]}");
            File dir = new File(getContext().getFilesDir(), "gerfex_runtime_data/external_models");
            if (!dir.exists()) {
                dir.mkdirs();
            }

            File file = new File(dir, "registry.json");
            FileWriter writer = new FileWriter(file, false);
            writer.write(registryJson);
            writer.close();

            ret.put("ok", true);
            ret.put("path", file.getAbsolutePath());
            call.resolve(ret);
        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }


    @PluginMethod
    public void testExternalModel(PluginCall call) {
        String name = call.getString("name", "");
        new Thread(() -> {
            JSObject ret = new JSObject();
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getContext()));
                }

                File file = new File(getContext().getFilesDir(), "gerfex_runtime_data/external_models/registry.json");
                StringBuilder sb = new StringBuilder();

                if (file.exists()) {
                    BufferedReader br = new BufferedReader(new FileReader(file));
                    String line;
                    while ((line = br.readLine()) != null) {
                        sb.append(line).append("\n");
                    }
                    br.close();
                }

                Python py = Python.getInstance();
                PyObject gateway = py.getModule("GerfexIntegratedV1.internal_intelligence.gerfex_entry_gate.gate");
                String json = gateway.callAttr(
                    "gerfex_to_external_model",
                    "test_external_model_connection",
                    name
                ).toString();

                ret.put("ok", true);
                ret.put("registry_path", file.getAbsolutePath());
                ret.put("registry_exists", file.exists());
                ret.put("registry_length", sb.length());
                ret.put("result", json);
                call.resolve(ret);
            } catch (Exception e) {
                ret.put("ok", false);
                ret.put("error", e.toString());
                call.resolve(ret);
            }
        }).start();
    }

    @PluginMethod
    public void readExternalModels(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            File file = new File(getContext().getFilesDir(), "gerfex_runtime_data/external_models/registry.json");
            if (!file.exists()) {
                ret.put("ok", true);
                ret.put("content", "{\"version\":\"EXTERNAL_MODELS_REGISTRY_V1\",\"mode\":\"advisor_only\",\"active\":[],\"providers\":[]}");
                ret.put("path", file.getAbsolutePath());
                call.resolve(ret);
                return;
            }

            BufferedReader br = new BufferedReader(new FileReader(file));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
            br.close();

            ret.put("ok", true);
            ret.put("content", sb.toString());
            ret.put("path", file.getAbsolutePath());
            call.resolve(ret);
        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }


    private String callWorkshopJson(String moduleName, String functionName, Object... args) {
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getContext()));
            }

            Python py = Python.getInstance();
            PyObject mod = py.getModule(moduleName);
            PyObject result = mod.callAttr(functionName, args);
            return py.getModule("json").callAttr("dumps", result).toString();

        } catch (Exception e) {
            try {
                JSONObject err = new JSONObject();
                err.put("ok", false);
                err.put("error", e.toString());
                return err.toString();
            } catch (Exception ignored) {
                return "{\"ok\":false,\"error\":\"workshop_error\"}";
            }
        }
    }

    @PluginMethod
    public void openWorkshopItem(PluginCall call) {
        JSObject ret = new JSObject();
        String path = call.getString("path", "");
        String result = callWorkshopJson(
            "GerfexIntegratedV1.development.workshop.open_item",
            "open_item",
            path
        );
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void saveWorkshopItem(PluginCall call) {
        JSObject ret = new JSObject();
        String path = call.getString("path", "");
        String content = call.getString("content", "");
        String result = callWorkshopJson(
            "GerfexIntegratedV1.development.workshop.save_item",
            "save_item",
            path,
            content
        );
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void deleteWorkshopItem(PluginCall call) {
        JSObject ret = new JSObject();
        String path = call.getString("path", "");
        Integer lineNumber = call.getInt("line_number", -1);
        Boolean recursive = call.getBoolean("recursive", true);

        String result = callWorkshopJson(
            "GerfexIntegratedV1.development.workshop.delete_item",
            "delete_item",
            path,
            lineNumber,
            recursive
        );
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void runWorkshopTest(PluginCall call) {
        JSObject ret = new JSObject();
        String result = callWorkshopJson(
            "GerfexIntegratedV1.development.workshop.basic_test",
            "run_basic_test"
        );
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }



    private String callGerfexEntryJson(String functionName) {
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getContext()));
            }

            Python py = Python.getInstance();
            PyObject entry = py.getModule("gerfex_entry");
            return entry.callAttr(functionName).toString();

        } catch (Exception e) {
            try {
                JSONObject err = new JSONObject();
                err.put("ok", false);
                err.put("error", e.toString());
                return err.toString();
            } catch (Exception ignored) {
                return "{\"ok\":false,\"error\":\"gerfex_entry_call_failed\"}";
            }
        }
    }


    private File ensureGmaModelFile() throws Exception {
        final String assetPath = "GerfexModels/google_gemma-3-4b-it-Q2_K.gguf";

        File dir = new File(getContext().getFilesDir(), "GerfexModels");
        if (!dir.exists() && !dir.mkdirs() && !dir.exists()) {
            throw new IOException("Failed to create GerfexModels dir: " + dir.getAbsolutePath());
        }

        File out = new File(dir, "google_gemma-3-4b-it-Q2_K.gguf");

        android.content.res.AssetFileDescriptor afd = null;
        long assetSize = 1729028512L;
        try {
            afd = getContext().getAssets().openFd(assetPath);
            long detectedSize = afd.getLength();
            if (detectedSize > 0L) assetSize = detectedSize;
        } catch (Exception ignored) {
            android.util.Log.w("GMA_DEBUG", "GMA asset openFd failed; using expected assetSize=" + assetSize);
        } finally {
            if (afd != null) {
                try { afd.close(); } catch (Exception ignored) {}
            }
        }

        if (out.exists()) {
            long existing = out.length();
            if (assetSize > 0L && existing == assetSize) {
                android.util.Log.i("GMA_DEBUG", "GMA model already present size=" + existing);
                return out;
            }
            android.util.Log.w("GMA_DEBUG", "GMA model invalid/incomplete, deleting old copy. existing=" + existing + " asset=" + assetSize);
            if (!out.delete()) {
                throw new IOException("Failed to delete invalid model file: " + out.getAbsolutePath() + " size=" + existing);
            }
        }

        android.util.Log.i("GMA_DEBUG", "Copying GMA model from assets to " + out.getAbsolutePath() + " assetSize=" + assetSize);

        InputStream in = null;
        OutputStream os = null;
        try {
            in = getContext().getAssets().open(assetPath);
            os = new FileOutputStream(out, false);
            byte[] buf = new byte[1024 * 1024];
            int n;
            long written = 0L;
            while ((n = in.read(buf)) > 0) {
                os.write(buf, 0, n);
                written += n;
            }
            os.flush();
            try {
                if (os instanceof FileOutputStream) {
                    ((FileOutputStream) os).getFD().sync();
                }
            } catch (Exception ignored) {}

            long finalSize = out.length();
            android.util.Log.i("GMA_DEBUG", "GMA model copy finished written=" + written + " finalSize=" + finalSize + " assetSize=" + assetSize);

            if (assetSize > 0L && finalSize != assetSize) {
                throw new IOException("Copied GGUF size mismatch. final=" + finalSize + " asset=" + assetSize);
            }
            if (finalSize < 100000000L) {
                throw new IOException("Copied GGUF unexpectedly too small: " + finalSize);
            }
            return out;
        } finally {
            if (os != null) {
                try { os.close(); } catch (Exception ignored) {}
            }
            if (in != null) {
                try { in.close(); } catch (Exception ignored) {}
            }
        }
    }

    @PluginMethod
    public void gmaNativeChat(PluginCall call) {
        /*
         * Run legacy GMA route off the plugin/UI path.
         *
         * We still keep the approved route:
         * thinkMain -> gerfex_entry.think_main -> main_surface
         * -> internal_intelligence/gma/main -> gerfex_entry_gate
         * -> fillGmaNativeIfNeeded -> GmaLlamaBridge
         *
         * But we execute it on a worker thread because the native path
         * may block for model load / context init / decode.
         */
        new Thread(() -> {
            try {
                thinkMain(call);
            } catch (Throwable e) {
                try {
                    JSObject ret = new JSObject();
                    ret.put("ok", false);
                    ret.put("stage", "gma_native_thread_exception");
                    ret.put("error", String.valueOf(e));
                    call.resolve(ret);
                } catch (Throwable ignored) {}
            }
        }, "gerfex-gma-native-chat").start();
    }

    @PluginMethod
    public void learningStatus(PluginCall call) {
        JSObject ret = new JSObject();
        String result = callGerfexEntryJson("learning_status");
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void approveLatestLesson(PluginCall call) {
        JSObject ret = new JSObject();
        String result = callGerfexEntryJson("approve_latest_lesson_entry");
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void approveLatestImprovement(PluginCall call) {
        JSObject ret = new JSObject();
        String result = callGerfexEntryJson("approve_latest_improvement_entry");
        ret.put("ok", true);
        ret.put("result", result);
        call.resolve(ret);
    }

    @PluginMethod
    public void startSpeech(PluginCall call) {
        try {
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ar-SA");
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "تكلم الآن");
            startActivityForResult(call, intent, "speechResult");
        } catch (Exception e) {
            call.reject("speech_start_failed: " + e.getMessage());
        }
    }

    @ActivityCallback
    private void speechResult(PluginCall call, ActivityResult result) {
        try {
            JSObject ret = new JSObject();

            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                ArrayList<String> matches = result.getData().getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                String text = "";
                if (matches != null && matches.size() > 0) text = matches.get(0);

                ret.put("ok", true);
                ret.put("text", text);
                call.resolve(ret);
                return;
            }

            ret.put("ok", false);
            ret.put("text", "");
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("speech_result_failed: " + e.getMessage());
        }
    }

}
