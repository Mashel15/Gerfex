import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.gerfex_api import app

client = TestClient(app)

r = client.get("/")
assert r.status_code == 200
assert r.json()["ok"]

r = client.get("/status")
assert r.status_code == 200
assert r.json()["ok"]

r = client.post("/think", json={"prompt": "حلل الشاشة الحالية", "model": "gerfex"})
assert r.status_code == 200
assert r.json()["ok"]
assert "result" in r.json()

print("API V1 OK")
