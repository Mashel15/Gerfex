package com.mashel15.gerfex;

import android.content.Intent;
import com.getcapacitor.annotation.ActivityCallback;
import androidx.activity.result.ActivityResult;
import android.speech.RecognizerIntent;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.net.Uri;
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
import java.io.FileOutputStream;
import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.TimeZone;

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
        File runtimeDir = new File(getContext().getFilesDir(), "gerfex_runtime_data/runtime");
        runtimeDir.mkdirs();
        return new File(runtimeDir, "execution_trace.jsonl");
    }

    private File executionPathFile() {
        File runtimeDir = new File(getContext().getFilesDir(), "gerfex_runtime_data/runtime");
        runtimeDir.mkdirs();
        return new File(runtimeDir, "execution_path.jsonl");
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

    @PluginMethod
    public void think(PluginCall call) {
        String message = call.getString("message", "");

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
                String result = entry.callAttr("think", message).toString();

                int nativeCount = executeFromResult(result);

                ret.put("ok", true);
                ret.put("result", result);
                ret.put("native_executed_count", nativeCount);
                ret.put("screen_text_saved_path", screenTextPath);

                call.resolve(ret);

            } catch (Exception e) {
                ret.put("ok", false);
                ret.put("error", e.toString());
                call.resolve(ret);
            }
        }).start();
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
