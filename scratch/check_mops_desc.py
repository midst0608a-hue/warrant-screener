import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

# Let's get the main page to see the title of t90sb03
res = requests.get("https://mopsov.twse.com.tw/mops/web/t90sb03", verify=False)
soup = BeautifulSoup(res.text, 'html.parser')
title = soup.title.string if soup.title else 'No title'
print("Page Title:", title)

# Also check any headers or warning on the table
res_ajax = requests.post("https://mopsov.twse.com.tw/mops/web/ajax_t90sb03", data={'encodeURIComponent': '1', 'step': '1', 'firstin': '1', 'TYPEK': 'sii'}, verify=False)
soup_ajax = BeautifulSoup(res_ajax.text, 'html.parser')
print("Table descriptions:")
for b in soup_ajax.find_all(['h2', 'h3', 'b', 'th']):
    print("-", b.text)
