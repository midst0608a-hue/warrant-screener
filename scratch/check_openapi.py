import requests
import json

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False)
try:
    data1 = r1.json()
    print("TWSE fields:", list(data1[0].keys()) if data1 else "Empty")
except Exception as e:
    print("TWSE parser error:", e)

r2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue", verify=False, timeout=10)
try:
    data2 = r2.json()
    print("TPEx fields:", list(data2[0].keys()) if data2 else "Empty")
except Exception as e:
    print("TPEx parser error:", e)
