package com.mashel15.gerfex;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

public class GerfexAccessibilityService extends AccessibilityService {
    public static GerfexAccessibilityService instance;
    public static String lastScreenText = "";

    @Override
    public void onServiceConnected() {
        instance = this;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root != null) {
            lastScreenText = collectText(root);
            root.recycle();
        }
    }

    @Override
    public void onInterrupt() {}

    private String collectText(AccessibilityNodeInfo node) {
        StringBuilder sb = new StringBuilder();
        collect(node, sb, 0);
        return sb.toString();
    }

    private void collect(AccessibilityNodeInfo node, StringBuilder sb, int depth) {
        if (node == null || depth > 20) return;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();

        if (text != null && text.length() > 0) {
            sb.append(text).append("\n");
        }
        if (desc != null && desc.length() > 0) {
            sb.append(desc).append("\n");
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                collect(child, sb, depth + 1);
                child.recycle();
            }
        }
    }

    public static boolean isReady() {
        return instance != null;
    }

    public static boolean pressBack() {
        if (instance == null) return false;
        return instance.performGlobalAction(GLOBAL_ACTION_BACK);
    }

    public static boolean pressHome() {
        if (instance == null) return false;
        return instance.performGlobalAction(GLOBAL_ACTION_HOME);
    }

    public static boolean tap(float x, float y) {
        if (instance == null) return false;

        Path path = new Path();
        path.moveTo(x, y);

        GestureDescription.StrokeDescription stroke =
                new GestureDescription.StrokeDescription(path, 0, 80);

        GestureDescription gesture =
                new GestureDescription.Builder().addStroke(stroke).build();

        return instance.dispatchGesture(gesture, null, null);
    }

    public static boolean swipe(float x1, float y1, float x2, float y2, long duration) {
        if (instance == null) return false;

        Path path = new Path();
        path.moveTo(x1, y1);
        path.lineTo(x2, y2);

        GestureDescription.StrokeDescription stroke =
                new GestureDescription.StrokeDescription(path, 0, duration);

        GestureDescription gesture =
                new GestureDescription.Builder().addStroke(stroke).build();

        return instance.dispatchGesture(gesture, null, null);
    }

    public static String dumpText() {
        return lastScreenText == null ? "" : lastScreenText;
    }
}
