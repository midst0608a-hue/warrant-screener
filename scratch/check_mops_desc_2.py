import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

res_ajax = requests.post("https://mopsov.twse.com.tw/mops/web/ajax_t90sb03", data={'encodeURIComponent': '1', 'step': '1', 'firstin': '1', 'TYPEK': 'sii'}, verify=False)
res_ajax.encoding = 'utf-8' # Let's see if MOPS returns utf-8
soup_ajax = BeautifulSoup(res_ajax.text, 'html.parser')
for b in soup_ajax.find_all(['h2', 'h3', 'b', 'th']):
    print("-", b.text)
