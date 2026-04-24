import requests

try:
    r = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", verify=False, timeout=10)
    data = r.json()
    mapping = {}
    for i in data:
        code = str(i.get('Code')).strip()
        name = str(i.get('Name')).strip()
        mapping[name] = code
    
    # Check if 聯發科 matches
    print("聯發科 in mapping?", "聯發科" in mapping)
    print("聯發科 code:", mapping.get("聯發科"))
except Exception as e:
    print(e)
