import os
from pathlib import Path

APP_HOME = Path(os.environ.get("GERFEX_APP_HOME", os.path.join(os.getcwd(), "gerfex_runtime_data")))

def app_path(*parts):
    p = APP_HOME.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def ensure_dirs():
    for name in ["learning", "memory", "runtime", "logs", "queue"]:
        (APP_HOME / name).mkdir(parents=True, exist_ok=True)
    return APP_HOME
