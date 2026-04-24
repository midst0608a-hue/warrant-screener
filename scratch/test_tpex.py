import requests
import json
import urllib3
urllib3.disable_warnings()

url = "https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue"
r = requests.get(url, verify=False, timeout=10)
if r.status_code == 200:
    data = r.json()
    if data:
        print("keys:", data[0].keys())
        print("demo 0:", data[0])
    else:
        print("Empty data")
else:
    print("Status:", r.status_code)

