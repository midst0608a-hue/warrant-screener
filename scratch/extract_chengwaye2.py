import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://chengwaye.com/disposal-forecast/"
res = requests.get(url, headers=headers, verify=False, timeout=10)
soup = BeautifulSoup(res.text, 'html.parser')
tables = soup.find_all('table')

def safe_print(obj):
    print(str(obj).encode('ascii', 'ignore').decode('ascii'))

for i, table in enumerate(tables):
    rows = table.find_all('tr')
    print(f"--- Table {i} ({len(rows)} rows) ---")
    for r_idx, row in enumerate(rows[:3]):
        cols = row.find_all(['td', 'th'])
        safe_print(f"Row {r_idx}: {[c.text.strip() for c in cols]}")

