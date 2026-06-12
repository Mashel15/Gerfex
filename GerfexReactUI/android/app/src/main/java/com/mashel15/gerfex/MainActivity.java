package com.mashel15.gerfex;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(GerfexPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
