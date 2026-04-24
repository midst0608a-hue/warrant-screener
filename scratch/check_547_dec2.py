import requests
import json

r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)

# The correct way to decode TWSE open data when it has mojibake
# It might be UTF-8 but requests misunderstood it, or it is big5
# Let's inspect raw bytes
raw_bytes = r1.content[:500]
print("Raw bytes start:", raw_bytes)

# Let's try to decode content directly
try:
    decoded = r1.content.decode('utf-8')
    data = json.loads(decoded)
    print("UTF-8 loads success")
    for i in data:
        if i.get('權證代號') == '055547':
            print("Stock:", i.get('標的證券/指數'))
            break
except Exception as e:
    print("UTF-8 fail:", e)

try:
    decoded = r1.content.decode('big5')
    data = json.loads(decoded)
    print("Big5 loads success!")
    for i in data:
        if i.get('權證代號') == '055547':
            print("Stock:", i.get('標的證券/指數'))
            break
except Exception as e:
    print("Big5 fail:", e)

