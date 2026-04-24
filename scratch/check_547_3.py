import requests

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)
data1 = r1.json()

r2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue", verify=False, timeout=10)
data2 = r2.json()

for i in data1:
    if str(i.get('權證代號')).strip() == '055547':
        print("TWSE:", i.get('權證簡稱'), "=>", i.get('標的證券/指數'))

for i in data2:
    if str(i.get('Code')).strip() == '055547':
        print("TPEx:", i.get('Name'), "=>", i.get('UnderlyingStockCode'))

