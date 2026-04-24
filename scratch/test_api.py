import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}
# Test TWSE
url = "https://www.twse.com.tw/zh/api/getSummary?prc=xxx" # wait, the twse URL was:
twse_url = "https://www.twse.com.tw/zh/warrant/info?warrantNo=030573"
res = requests.get(twse_url, headers=headers)
print("TWSE Code:", res.status_code)
# It's an HTML page or API? Let's check if it's html.
if "<html>" in res.text[:200].lower() or "<!doctype" in res.text[:200].lower():
    print("TWSE returned HTML")
else:
    print("TWSE returned JSON/other")

# Let's try SinoTrade API
# SinoTrade usually has an XHR endpoint for their warrant search page.
# However, finding it without a browser is tricky. We'll try to use `requests` on their search page to see what we get.
sino_url = "https://warrant.sinotrade.com.tw/want/wSearch.aspx"
sino_res = requests.get(sino_url, headers=headers)
print("SinoTrade Status:", sino_res.status_code)
