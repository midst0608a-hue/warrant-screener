import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Test Chengwaye
res = requests.get("https://chengwaye.com/disposal-forecast/", headers=headers, verify=False, timeout=10)
soup = BeautifulSoup(res.text, 'html.parser')
tables = soup.find_all('table')
print("Chengwaye tables found:", len(tables))

# 2. Test TWSE Outstanding Ratio
url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&type=029999" # Let's see if this endpoint works
res2 = requests.get(url, headers=headers)
print("MI_INDEX 029999 keys:", res2.json().keys() if res2.status_code == 200 else "Fail")

url_ratio = "https://www.twse.com.tw/exchangeReport/MI_INDEX_WARRANT?response=json"
res3 = requests.get(url_ratio, headers=headers)
print("MI_INDEX_WARRANT keys:", res3.json().keys() if res3.status_code == 200 and 'json' in res3.headers.get('content-type', '').lower() else "Fail")

# What if it's open data?
# https://openapi.twse.com.tw/v1/opendata/t187ap45_L (上市認購(售)權證在外流通單位數)
res4 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap45_L", verify=False)
if res4.status_code == 200:
    data = res4.json()
    if len(data) > 0:
        print("t187ap45_L keys:", data[0].keys())
