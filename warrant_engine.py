import requests
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import norm
import datetime
import re
import urllib3
from bs4 import BeautifulSoup
import io
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. BS 計算引擎 ---
def bs_price_delta(S, K, T, r, sigma, opt_type):
    try:
        S, K, T, r, sigma = float(S), float(K), float(T), float(r), float(sigma)
        if T <= 0: return (max(0.0, S-K) if opt_type=='C' else max(0.0, K-S)), 0.0
        d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if opt_type == 'C':
            return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2), norm.cdf(d1)
        else:
            return K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1), norm.cdf(d1) - 1.0
    except: return 0.0, 0.0

# --- 2. 標的報價獲取 ---
def get_stock_info(stock_id):
    stock_id = str(stock_id).strip()
    
    # 處理指數型權證代號對應
    if '指' in stock_id or stock_id.upper() in ['TX', 'MTX', 'IX0001', 'TAIEX']:
        ticker_list = ['^TWII']
    else:
        ticker_list = [f"{stock_id}.TW", f"{stock_id}.TWO"]
        
    for ticker in ticker_list:
        try:
            s = yf.Ticker(ticker)
            hist = s.history(period="3mo")
            hist = hist.dropna(subset=['Close']) # 過濾盤中或收盤時的 NaN
            if not hist.empty:
                p = hist['Close'].iloc[-1]
                sig = np.log(hist['Close'] / hist['Close'].shift(1)).std() * np.sqrt(252)
                return p, sig, stock_id
        except: continue
    return None, 0.3, stock_id

# --- 3. 獲取全市場權證資料 (結合規格) ---
def load_all_warrants():
    full_list = []
    
    # 建立上市股票代號對應字典 (解決 TWSE OpenAPI 只有中文名稱的問題)
    stock_mapping = {}
    try:
        r_map = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", verify=False, timeout=10)
        if r_map.status_code == 200:
            for item in r_map.json():
                code = str(item.get('Code', '')).strip()
                name = str(item.get('Name', '')).strip()
                if name: stock_mapping[name] = code
    except: pass
    
    #上市
    try:
        r1 = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap37_L", verify=False, timeout=10)
        if r1.status_code == 200:
            for i in r1.json():
                try:
                    raw_stock = str(i.get('標的證券/指數', '')).strip()
                    # 嘗試從 mapping 中取出數字代號，若無則保留原名 (例如台指期、ETF等)
                    actual_stock_id = stock_mapping.get(raw_stock, raw_stock.split(' ')[0])
                    
                    full_list.append({
                        'w_code': str(i.get('權證代號', '')).strip(),
                        'w_name': str(i.get('權證簡稱', '')).strip(),
                        'stock_id': actual_stock_id, 
                        'strike': float(i.get('最新履約價格(元)/履約指數', 0)),
                        'ratio': float(i.get('最新標的履約配發數量(每仟單位權證)', 0)),
                        'expiry': str(i.get('最後交易日', '')).strip(),
                        'market': '上市',
                        'opt_type': 'C' if '購' in str(i.get('權證簡稱', '')) else 'P'
                    })
                except: continue
    except: pass

    #上櫃
    try:
        r2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant_issue", verify=False, timeout=10)
        if r2.status_code == 200:
            for i in r2.json():
                try:
                    full_list.append({
                        'w_code': str(i.get('Code', '')).strip(),
                        'w_name': str(i.get('Name', '')).strip(),
                        'stock_id': str(i.get('UnderlyingStockCode', '')).strip(),
                        'strike': float(i.get('LatestExercisePrice', 0)),
                        'ratio': float(i.get('Latest ExerciseRatio', 0)),
                        'expiry': str(i.get('ExpiryDate', '')).strip(),
                        'market': '上櫃',
                        'opt_type': 'C' if '購' in str(i.get('Name', '')) else 'P'
                    })
                except: continue
    except: pass
    
    df = pd.DataFrame(full_list)
    if not df.empty:
        df = df[df['strike'] > 0]
    return df

# --- 4. 權證評分系統與指標計算 ---
def calculate_warrant_metrics(df_warrants, stock_price, sigma=0.4):
    results = []
    now = datetime.datetime.now()
    
    for idx, row in df_warrants.iterrows():
        try:
            exp_str = str(row['expiry']).replace('/', '').replace('.', '')
            if len(exp_str) == 7: 
                exp_str = str(int(exp_str) + 19110000)
            
            exp_date = datetime.datetime.strptime(exp_str, '%Y%m%d')
            days_left = (exp_date - now).days
            if days_left <= 0: continue
            
            ratio_raw = row['ratio']
            ratio = ratio_raw / 1000.0 if ratio_raw > 10 else ratio_raw
                
            K = row['strike']
            S = stock_price
            opt_type = row['opt_type']
            
            if opt_type == 'C':
                otm_pct = (K - S) / S * 100
            else:
                otm_pct = (S - K) / S * 100 
                
            theo_p, delta = bs_price_delta(S, K, days_left/365.0, 0.015, sigma, opt_type)
            warrant_price = theo_p * ratio
            
            if warrant_price <= 0.01: leverage = 0
            else: leverage = abs(delta * S / warrant_price * ratio)
                
            score = 0
            if 60 <= days_left <= 180: score += 30
            elif 30 <= days_left < 60: score += 15
            elif days_left > 180: score += 20
            # 將價外程度轉為「價內程度」：正值為價內，負值為價外
            itm_pct = -otm_pct
            
            if 3 <= leverage <= 7: score += 30
            elif 2 <= leverage < 3 or 7 < leverage <= 10: score += 15
            
            # 條件改為價外15%(-15%) 到 價內5%(+5%)，未滿足則扣分但保留
            if -15 <= itm_pct <= 5: 
                score += 40
            else:
                score -= 30
            
            results.append({
                '代號': row['w_code'],
                '名稱': row['w_name'],
                '市場': row['market'],
                '認購/售': '認購' if opt_type=='C' else '認售',
                '履約價': K,
                '行使比例': ratio,
                '剩餘天數': days_left,
                '價內程度(%)': round(itm_pct, 2),
                '理論價': round(warrant_price, 4),
                '實質槓桿': round(leverage, 2),
                '綜合評分': score,
            })
            
        except Exception as e: continue
            
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by='綜合評分', ascending=False)
    return df_res

# --- 5. 處置與注意股查詢 ---
def check_disposal_status(stock_id):
    stock_id = str(stock_id).strip()
    try:
        url = "https://chengwaye.com/disposal-forecast/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        tables = soup.find_all('table')
        
        # 優先檢查 Table 2: 目前已被處置
        if len(tables) > 2:
            for row in tables[2].find_all('tr'):
                cols = [c.text.strip() for c in row.find_all(['td', 'th'])]
                if len(cols) > 6 and cols[1] == stock_id:
                    mins = cols[3]
                    out_date = cols[6]
                    return True, f"此標的已被處置 ({mins}分鐘撮合)，預計出關日期：{out_date}"

        # 若未被處置，檢查 Table 0 & 1: 處置預測 (注意股)
        for i in range(min(2, len(tables))):
            for row in tables[i].find_all('tr'):
                cols = [c.text.strip() for c in row.find_all(['td', 'th'])]
                if len(cols) > 5 and cols[1] == stock_id:
                    msg = cols[5]
                    return True, f"目前列為注意股！最快處置預測：{msg}"
        
    except Exception as e:
        print("Disposal parse error:", e)
    return False, ""

# --- 6. 取得造市專戶庫存不足之權證黑名單 (MOPS) ---
def get_low_liquidity_warrants():
    # 回傳集合 (Set)，包含所有庫存不足 500 張的權證代碼
    black_list = set()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 上市
    try:
        url_twse = "https://mopsov.twse.com.tw/mops/web/ajax_t90sb03"
        payload_twse = {'encodeURIComponent': '1', 'step': '1', 'firstin': '1', 'TYPEK': 'sii'}
        r_twse = requests.post(url_twse, headers=headers, data=payload_twse, verify=False, timeout=10)
        dfs = pd.read_html(io.StringIO(r_twse.text))
        for df in dfs:
            if '權證代號' in df.columns:
                black_list.update(df['權證代號'].astype(str).tolist())
    except: pass
    
    # 上櫃
    try:
        url_tpex = "https://mopsov.twse.com.tw/mops/web/ajax_o_t90sb03"
        payload_tpex = {'encodeURIComponent': '1', 'step': '1', 'firstin': '1', 'TYPEK': 'otc'}
        r_tpex = requests.post(url_tpex, headers=headers, data=payload_tpex, verify=False, timeout=10)
        dfs = pd.read_html(io.StringIO(r_tpex.text))
        for df in dfs:
            if '權證代號' in df.columns:
                black_list.update(df['權證代號'].astype(str).tolist())
    except: pass
    
    return black_list