import requests

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)
for i in r1.json():
    w_code = str(i.get('權證代號', '')).strip()
    if w_code == '055547':
        print(i)
