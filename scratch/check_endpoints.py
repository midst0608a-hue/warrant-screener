import requests

endpoints = [
    "t187ap03_L", # 基本資料?
    "t187ap44_L",
]
for ep in endpoints:
    url = f"https://openapi.twse.com.tw/v1/opendata/{ep}"
    try:
        r = requests.get(url, verify=False, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"{ep} keys:", list(data[0].keys()))
                print(f"{ep} first item:", [data[0][k] for k in list(data[0].keys())[:5]])
    except Exception as e:
        print(ep, "failed:", e)
