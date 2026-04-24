import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd
import io
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Chengwaye disposal
print("--- Chengwaye ---")
try:
    res = requests.get("https://chengwaye.com/disposal-forecast/", headers=headers, verify=False, timeout=10)
    dfs = pd.read_html(io.StringIO(res.text))
    print("Num tables:", len(dfs))
    if dfs:
        for i, df in enumerate(dfs):
            print(f"-- Table {i} --")
            print(df.head(2).to_dict())
            if '股票名稱' in str(df) or '標的' in str(df) or '名稱' in str(df) or '代號' in str(df) or '股票' in str(df):
                print(f"Table {i} matches!")
except Exception as e:
    print(e)
    
# 2. t187ap45_L
print("--- t187ap45_L ---")
try:
    res4 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap45_L", verify=False, timeout=10)
    if res4.status_code == 200:
        data = res4.json()
        print("Keys:", data[0].keys() if data else "Empty")
        print("Demo:", data[0] if data else "Empty")
except Exception as e:
    print(e)

# 3. TPEx Ratio
print("--- TPEx Ratio ---")
try:
    res_tpex = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_ratio", verify=False, timeout=10) # Maybe this endpoint exists?
    print("TPEx openapi ratio code:", res_tpex.status_code)
except Exception as e:
    print(e)
