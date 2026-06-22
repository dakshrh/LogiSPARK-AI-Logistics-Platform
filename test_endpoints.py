import requests
import json

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    ("GET", "/"),
    ("GET", "/api/platform-stats"),
    ("GET", "/api/shipments"),
    ("GET", "/api/stats"),
    ("POST", "/api/hs-classify", {"query": "Leather handbag"}),
    ("POST", "/api/emergency-plan", {
        "transport_type": "Ocean",
        "severity": "high",
        "origin": "Mumbai",
        "destination": "Delhi",
        "cargo_value": 1000000.0,
        "current_delay_hrs": 24.0
    }),
    ("POST", "/api/risk-assess", {
        "origin": "Mumbai",
        "destination": "Delhi",
        "mode": "Ocean",
        "cargo_type": "Electronics",
        "cargo_value": 1000000.0,
        "route_region": ""
    }),
    ("GET", "/predict/LS1001"),
    ("GET", "/predict/LS1001/json")
]

all_passed = True

for method, url, *body in endpoints:
    full_url = f"{BASE_URL}{url}"
    try:
        if method == "GET":
            res = requests.get(full_url)
        else:
            res = requests.post(full_url, json=body[0])
            
        if res.status_code == 200:
            print(f"[OK] {method} {url}")
        else:
            print(f"[FAIL] {method} {url} - Status: {res.status_code}")
            print(res.text[:200])
            all_passed = False
    except Exception as e:
        print(f"[ERROR] {method} {url} - {str(e)}")
        all_passed = False

if all_passed:
    print("\nALL TESTS PASSED: Zero Validation Errors")
else:
    print("\nSOME TESTS FAILED")
