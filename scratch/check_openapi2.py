import requests
import json

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False)
data1 = r1.json()
print("TWSE 1st item:", list(data1[0].keys()))

r2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue", verify=False)
data2 = r2.json()
print("TPEx 1st item:", data2[0])
