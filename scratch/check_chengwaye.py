import requests
import pandas as pd
import io
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_disposal_list():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://chengwaye.com/disposal-forecast/"
    try:
        res = requests.get(url, headers=headers, verify=False, timeout=10)
        dfs = pd.read_html(io.StringIO(res.text))
        disposal_stocks = []
        for df in dfs:
            # Table might have '股票名稱' or '代號'
            df_str = df.astype(str)
            for idx, row in df.iterrows():
                for col in df.columns:
                    val = str(row[col])
                    # Try to find anything that looks like a stock code or name
                    # Just combine all texts in the row and we can do a substring check later
                    pass
            
            # Actually easier: just dump the entire table text into a single string for substring checking!
            # If the user searches "2330" or "台積電", we just check if it's in the text!
            
        # Let's see what the tables actually contain
        for i, df in enumerate(dfs):
            print(f"Table {i} columns:", list(df.columns))
            if len(df) > 0:
                print(f"Table {i} row 0:", dict(df.iloc[0]))
    except Exception as e:
        print("Error:", e)

get_disposal_list()
