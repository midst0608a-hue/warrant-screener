import requests

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)
# Force encoding to big5 or utf-8 depending on what works
r1.encoding = 'utf-8' # Let's try utf-8 first
try:
    for i in r1.json():
        if str(i.get('權證代號')).strip() == '055547':
            print("UTF-8 decoded:", i.get('標的證券/指數'), i.get('權證簡稱'))
except: pass

r1.encoding = 'big5'
try:
    for i in r1.json():
        if str(i.get('權證代號', '')).strip() == '055547':
             print("BIG5 decoded:", i.get('標的證券/指數'), i.get('權證簡稱'))
except: pass
