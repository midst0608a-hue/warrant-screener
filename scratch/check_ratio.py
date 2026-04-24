import requests
import urllib3
urllib3.disable_warnings()
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&type=029999" 
    res = requests.get(url, headers=headers, verify=False, timeout=10)
    data = res.json()
    print("MI_INDEX keys:", data.keys())
    if 'data9' in data: # Usually data9 contains warrant quotes, maybe it has outstanding ratio?
        print("data9 headers:", data['fields9'])
except Exception as e:
    print("MI_INDEX fail:", e)

try:
    url_ratio = "https://www.twse.com.tw/exchangeReport/MI_INDEX_WARRANT?response=json"
    res2 = requests.get(url_ratio, headers=headers, verify=False, timeout=10)
    print("url_ratio OK:", res2.status_code) # This usually requires params like dates or gives a huge list
except Exception as e:
    print("url_ratio fail:", e)

try:
    url_otc_ratio = "https://www.tpex.org.tw/openapi/v1/tpex_warrant_ratio"
    res3 = requests.get(url_otc_ratio, headers=headers, verify=False, timeout=10)
    if res3.status_code == 200:
        print("tpex_warrant_ratio fields:", res3.json()[0].keys() if res3.json() else "Empty")
except Exception as e:
    print("tpex_warrant_ratio fail:", e)
