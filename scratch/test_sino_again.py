import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
}
try:
    url = "https://warrant.sinotrade.com.tw/want/wSearch.aspx"
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    print("SinoTrade Status:", r.status_code)
    # let's look for "warrant/ws/" or similar endpoints
    import re
    apis = re.findall(r"['\"](/[\w/.\-]+)['\"]", r.text)
    ajax = re.findall(r"\.ajax\(\{[\s\S]+?url\s*:\s*['\"]([^'\"]+)['\"]", r.text)
    print("Found APIs:", list(set(apis))[:20])
    print("Found AJAX calls:", list(set(ajax)))
except Exception as e:
    print(e)
