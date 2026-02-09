import requests
import sys

try:
    print("Pinging http://localhost:8000/ ...")
    r = requests.get("http://localhost:8000/", timeout=2)
    print(f"Root Status: {r.status_code}")
    
    print("Pinging http://localhost:8000/api/v1/system/status ...")
    r2 = requests.get("http://localhost:8000/api/v1/system/status", timeout=2)
    print(f"Status Endpoint: {r2.status_code}")
    print(r2.text)
except Exception as e:
    print(f"Connection Failed: {e}")
