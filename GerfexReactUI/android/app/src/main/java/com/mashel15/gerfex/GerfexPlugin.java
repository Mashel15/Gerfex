package com.mashel15.gerfex;

import android.content.Intent;
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

@CapacitorPlugin(name = "Gerfex")
public class GerfexPlugin extends Plugin {

    private String mapPackage(String name) {
        if (name == null) return "";
        String p = name.toLowerCase();
        if (p.equals("chrome")) return "android.intent.web";
        if (p.equals("youtube")) return "android.intent.youtube";
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

            if ("android.intent.web".equals(mapped)) {
                return openUrl("https://www.google.com");
            }

            if ("android.intent.youtube".equals(mapped)) {
                return openUrl("https://www.youtube.com");
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
                Intent intent = new Intent(Intent.ACTION_MAIN);
                intent.addCategory(Intent.CATEGORY_HOME);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                return true;
            }

            if ("press_back".equals(name)) {
                return false; // يحتاج Accessibility لاحقاً
            }

            if ("wait".equals(name)) {
                try { Thread.sleep(args.optInt("seconds", 1) * 1000L); } catch(Exception ignored) {}
                return true;
            }

            if ("dump_ui".equals(name)) {
                return false; // يحتاج Accessibility لاحقاً
            }

            return false;

        } catch (Exception e) {
            return false;
        }
    }

    private int executeFromResult(String result) {
        int count = 0;
        try {
            JSONObject root = new JSONObject(result);
            JSONObject raw = root.optJSONObject("raw");
            if (raw == null) return 0;

            JSONObject execution = raw.optJSONObject("execution");
            if (execution == null) return 0;

            JSONObject decision = execution.optJSONObject("decision");
            if (decision == null) decision = raw.optJSONObject("decision");
            if (decision == null) return 0;

            JSONArray actions = decision.optJSONArray("actions");
            if (actions != null) {
                for (int i = 0; i < actions.length(); i++) {
                    JSONObject a = actions.optJSONObject(i);
                    if (a != null && executeAction(a)) count++;
                }
                return count;
            }

            JSONObject action = decision.optJSONObject("action");
            if (action != null && executeAction(action)) count++;

        } catch (Exception ignored) {}

        return count;
    }

    @PluginMethod
    public void think(PluginCall call) {
        String message = call.getString("message", "");
        JSObject ret = new JSObject();

        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getContext()));
            }

            Python py = Python.getInstance();
            PyObject entry = py.getModule("gerfex_entry");
            String result = entry.callAttr("think", message).toString();

            int nativeCount = executeFromResult(result);

            ret.put("ok", true);
            ret.put("result", result);
            ret.put("native_executed_count", nativeCount);
            call.resolve(ret);

        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }
}
