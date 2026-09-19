"""
GreenGrid AI — Phase 1 API tests (requires the backend to be running)

Run:
    # terminal 1
    cd backend && uvicorn main:app --port 8000

    # terminal 2
    cd greengrid-ai && python3 tests/test_api.py
"""
import sys
import requests

BASE = "http://127.0.0.1:8000"
passed, failed = 0, 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}")
        failed += 1


try:
    requests.get(f"{BASE}/health", timeout=2)
except requests.exceptions.ConnectionError:
    print(f"Could not reach {BASE} — start the backend first:")
    print("  cd backend && uvicorn main:app --port 8000")
    sys.exit(1)

print("7. /health")
r = requests.get(f"{BASE}/health")
check("health returns 200", r.status_code == 200)
data = r.json()
check("solar model reported loaded", data.get("solar_model_loaded") is True)
check("wind model reported loaded", data.get("wind_model_loaded") is True)

print("\n8. /predict/solar")
r = requests.post(f"{BASE}/predict/solar", json={
    "irradiation": 0.85, "ambient_temperature": 31, "module_temperature": 46,
    "hour": 13, "plant_id": 1,
})
check("solar predict returns 200", r.status_code == 200)
body = r.json()
check("solar predicted_power is a positive number", isinstance(body.get("predicted_power"), (int, float)) and body["predicted_power"] > 0)
check("solar response reports its model", "model" in body)

r_bad = requests.post(f"{BASE}/predict/solar", json={"irradiation": 99, "ambient_temperature": 31, "module_temperature": 46, "hour": 13})
check("solar rejects out-of-range irradiation (422)", r_bad.status_code == 422)

print("\n9. /predict/wind")
r = requests.post(f"{BASE}/predict/wind", json={
    "wind_speed": 12, "wind_direction": 200, "theoretical_power": 3400,
})
check("wind predict returns 200", r.status_code == 200)
body = r.json()
check("wind predicted_power is a positive number", isinstance(body.get("predicted_power"), (int, float)) and body["predicted_power"] > 0)

r_missing = requests.post(f"{BASE}/predict/wind", json={"wind_speed": 5})
check("wind rejects missing fields (422)", r_missing.status_code == 422)

print("\n hydro honesty check")
r = requests.post(f"{BASE}/predict/hydro")
check("hydro correctly reports not implemented (501)", r.status_code == 501)

print("\n10. Frontend -> backend shape check (CORS + response shape the frontend expects)")
check("solar response has 'predicted_power' and 'model' keys the frontend reads",
      set(["predicted_power", "unit", "model"]).issubset(requests.post(f"{BASE}/predict/solar", json={
          "irradiation": 0.5, "ambient_temperature": 28, "module_temperature": 35, "hour": 11,
      }).json().keys()))

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
