import os
from pathlib import Path

DEFAULT_APK_HOME = Path("/data/data/com.mashel15.gerfex/files/gerfex_runtime_data")
TERMUX_FALLBACK_HOME = Path(__file__).resolve().parent / "runtime" / "termux_runtime_data"

_env_home = os.environ.get("GERFEX_APP_HOME")

if _env_home:
    APP_HOME = Path(_env_home)
else:
    try:
        DEFAULT_APK_HOME.mkdir(parents=True, exist_ok=True)
        APP_HOME = DEFAULT_APK_HOME
    except Exception:
        APP_HOME = TERMUX_FALLBACK_HOME

def app_path(*parts):
    p = APP_HOME.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def ensure_dirs():
    for name in ["development", "learning", "memory", "runtime", "logs", "queue"]:
        (APP_HOME / name).mkdir(parents=True, exist_ok=True)
    return APP_HOME
