import requests

url = "https://warrant.sinotrade.com.tw/want/wSearch.aspx"
res = requests.get(url, verify=False)
print("SinoTrade Search Code:", res.status_code)
# Search if there is any API endpoint like WaitData or API in script
import re
apis = set(re.findall(r"['\"](/[\w/.]*api[\w/.]*)['\"]", res.text, re.IGNORECASE))
ajax = set(re.findall(r"['\"]([\w/.]+\.asmx/[\w/.]+)['\"]", res.text, re.IGNORECASE))
print("APIs:", apis)
print("AJAX:", ajax)

url_api = "https://www.tpex.org.tw/web/derivative/warrant/info/result.php?stk_code=700682"
r_tpex = requests.get(url_api, verify=False, timeout=8)
print("TPex HTML length:", len(r_tpex.text))
if "標的" in r_tpex.text:
    print("TPex has warrant info!")
else:
    print("TPex doesn't have warrant info")
