import requests
import json
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# Test 1: chengwaye.com
url_disp = "https://chengwaye.com/disposal-forecast/"
try:
    r = requests.get(url_disp, headers=headers, timeout=10, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')
    # find something that looks like stock names or codes
    print("ChengWaYe length:", len(r.text))
    if '處置' in r.text:
       print("Found 處置 in text")
    
except Exception as e:
    print("ChengWaYe Error:", e)

# Test 2: TWSE Outstanding Ratio
url_twse_out = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&type=029999" # 029999 is warrant but let's check
url_twse_ratio = "https://www.twse.com.tw/exchangeReport/MI_INDEX_WARRANT?response=json" 
# Oh wait, maybe TWSE OPENAPI has it?
# Let's hit TWSE open api for warrants
r2 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap43_L", verify=False) # 權證發行規模? No, t187ap44_L failed.
try:
    # 找權證在外流通比率查詢API
    pass
except:
    pass

