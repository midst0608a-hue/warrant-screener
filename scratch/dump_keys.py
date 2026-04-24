import requests
import json
import codecs

headers = {'User-Agent': 'Mozilla/5.0'}
r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)
try:
    data1 = r1.json()
    with codecs.open(r"C:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器\scratch\keys1.json", "w", encoding="utf-8") as f:
        json.dump(list(data1[0].keys()), f, ensure_ascii=False)
except Exception as e:
    pass

r2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue", verify=False, timeout=10)
try:
    data2 = r2.json()
    with codecs.open(r"C:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器\scratch\keys2.json", "w", encoding="utf-8") as f:
        json.dump(list(data2[0].keys()), f, ensure_ascii=False)
except Exception as e:
    pass
