import requests
import json
import datetime

url = "http://localhost:8000/api/v1/ingest"
date_str = datetime.date.today().isoformat()

payload = {
    "text": "Testing ingest endpoint connectivity and upsert logic.",
    "date": date_str,
    "habits": ["testing"]
}

print(f"Sending POST to {url} with date {date_str}...")
try:
    r = requests.post(url, json=payload, timeout=20)
    print(f"Status Code: {r.status_code}")
    r.encoding = 'utf-8'
    print("Response:")
    try:
        print(r.text)
    except UnicodeEncodeError:
        print(r.text.encode('utf-8', errors='ignore').decode('utf-8'))
except Exception as e:
    print(f"Request Failed: {e}")
