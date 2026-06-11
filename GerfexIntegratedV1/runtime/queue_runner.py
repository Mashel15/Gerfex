import json
import os
import time
import subprocess
import shlex
from pathlib import Path

try:
    from runtime_state import record
except Exception:
    def record(*args, **kwargs):
        return None

QUEUE_FILE = str(Path(__file__).resolve().parent / "android_queue.txt")
RISH = os.path.expanduser("~/rish/rish")
SCREEN_FILE = "/sdcard/Download/gerfex_screen.png"

APPS = {
    "chrome": "com.android.chrome/com.google.android.apps.chrome.Main",
    "samsung": "com.sec.android.app.sbrowser/.SBrowserMainActivity",
    "settings": "com.android.settings/.Settings",
    "youtube": "com.google.android.youtube/com.google.android.apps.youtube.app.WatchWhileActivity"
}

def rish_cmd(command):
    print("RISH:", command)
    result = subprocess.run(
        [RISH, "-c", command],
        text=True,
        capture_output=True,
        env={**os.environ, "RISH_APPLICATION_ID": "com.termux"}
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

def run_cmd(cmd):
    print("RUN:", " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

def execute(item):
    action = item.get("action")
    args = item.get("args", {})
    record("runner_action", last_runner_action=item, status="running")

    if action == "open_url":
        url = args.get("url", "")
        if not url:
            print("OPEN_URL ERROR: missing url")
            return
        rish_cmd(f"am start -a android.intent.action.VIEW -d '{url}' -p com.android.chrome")
        print("BROWSER POLICY: chrome")
        return


    elif action == "open_app":
        component = APPS.get(args.get("package"))
        if component:
            rish_cmd(f"am start -n {component}")
        return

    if action == "open_settings":
        run_cmd(["am", "start", "-a", "android.settings.SETTINGS"])
        return

    if action == "key":
        keymap = {
            "HOME": "3",
            "BACK": "4",
            "RECENTS": "187",
            "ENTER": "66"
        }
        code = keymap.get(args.get("key"))
        if code:
            rish_cmd(f"input keyevent {code}")
        return
    if action == "press_back":
        rish_cmd("input keyevent 4")
        return

    if action == "press_home":
        rish_cmd("input keyevent 3")
        return

    if action == "press_recent":
        rish_cmd("input keyevent 187")
        return

    if action == "press_enter":
        rish_cmd("input keyevent 66")
        return


    if action == "tap":
        rish_cmd(f"input tap {int(args['x'])} {int(args['y'])}")
        return

    if action == "swipe":
        rish_cmd(
            f"input swipe {int(args['x1'])} {int(args['y1'])} "
            f"{int(args['x2'])} {int(args['y2'])} {int(args.get('duration', 500))}"
        )
        return

    if action == "type_text":
        safe = str(args.get("text", "")).replace(" ", "%s")
        rish_cmd("input text " + shlex.quote(safe))
        return

    if action == "wait":
        seconds = float(args.get("seconds", 1))
        print("WAIT:", seconds)
        time.sleep(seconds)
        return

    if action == "dump_ui":
        focus = args.get("focus")
        if focus:
            component = APPS.get(focus)
            if component:
                rish_cmd(f"am start -n {component}")
                time.sleep(1)
        rish_cmd("uiautomator dump /sdcard/Download/gerfex_ui.xml")
        print("UI DUMP SAVED: /sdcard/Download/gerfex_ui.xml")
        return

    if action == "screenshot":
        rish_cmd(f"screencap -p {SCREEN_FILE}")
        print("SCREENSHOT SAVED:", SCREEN_FILE)
        return

    print("UNKNOWN ACTION:", action)

def process_queue():
    if not os.path.exists(QUEUE_FILE):
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return

    open(QUEUE_FILE, "w").close()

    for line in lines:
        try:
            execute(json.loads(line))
            time.sleep(1)
        except Exception as e:
            print("ERROR:", e)
            record("error", last_error=str(e), status="error")

def main():
    print("Gerfex queue runner with vision started")
    while True:
        process_queue()
        time.sleep(1)

if __name__ == "__main__":
    main()
