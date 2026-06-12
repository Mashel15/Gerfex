package com.mashel15.gerfex;

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

            ret.put("ok", true);
            ret.put("result", result);
            call.resolve(ret);

        } catch (Exception e) {
            ret.put("ok", false);
            ret.put("error", e.toString());
            call.resolve(ret);
        }
    }
}
