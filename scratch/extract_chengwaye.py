import requests
import pandas as pd
import io
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://chengwaye.com/disposal-forecast/"
res = requests.get(url, headers=headers, verify=False, timeout=10)
dfs = pd.read_html(io.StringIO(res.text))

# Safe print for cp950 terminal
def safe_print(obj):
    print(str(obj).encode('ascii', 'ignore').decode('ascii'))

for idx, df in enumerate(dfs):
    print(f"--- Table {idx} ---")
    safe_print(list(df.columns))
    for i in range(min(2, len(df))):
        safe_print(dict(df.iloc[i]))

