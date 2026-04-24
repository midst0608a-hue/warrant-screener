import requests
import pandas as pd
import io
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0'
}

# 1. MOPS t90sb03 (TWSE Warrants > 80% outstanding)
print("--- MOPS TWSE ---")
try:
    url = "https://mopsov.twse.com.tw/mops/web/ajax_t90sb03"
    payload = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'TYPEK': 'sii',
    }
    # Often mops uses POST
    r = requests.post(url, headers=headers, data=payload, verify=False, timeout=10)
    print("Status:", r.status_code)
    dfs = pd.read_html(io.StringIO(r.text))
    print(f"Found {len(dfs)} tables")
    if dfs:
        for i, df in enumerate(dfs):
            if "權證名稱" in str(df) or "權證代號" in str(df):
                print(f"Table {i} is the target table. Head:")
                print(df.head(2))
except Exception as e:
    print(e)
    
# 2. MOPS o_t90sb03 (TPEx Warrants > 80% outstanding)
print("\n--- MOPS TPEx ---")
try:
    url = "https://mopsov.twse.com.tw/mops/web/ajax_o_t90sb03"
    payload['TYPEK'] = 'otc'
    r = requests.post(url, headers=headers, data=payload, verify=False, timeout=10)
    dfs = pd.read_html(io.StringIO(r.text))
    print(f"Found {len(dfs)} tables")
    for i, df in enumerate(dfs):
        if "權證名稱" in str(df) or "權證代號" in str(df):
            print(f"Table {i} is the target table. Head:")
            print(df.head(2))
except Exception as e:
    print(e)

# 3. WarrantWin (Yuanta)
print("\n--- Yuanta ---")
try:
    r = requests.get("https://www.warrantwin.com.tw/eyuanta/Warrant/Info.aspx", headers=headers, verify=False, timeout=10)
    print("Yuanta status:", r.status_code)
    print("Length of content:", len(r.text))
except Exception as e:
    print(e)

