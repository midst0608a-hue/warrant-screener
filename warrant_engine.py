import requests
import json
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
from urllib3.exceptions import InsecureRequestWarning
import warnings
import datetime

warnings.simplefilter('ignore', InsecureRequestWarning)

def resolve_stock_id(stock_name: str) -> str:
    """如果輸入是中文名稱(如台積電)，盡量轉換為代碼(如2330)"""
    if str(stock_name).isdigit() or str(stock_name).encode('utf-8').isalnum():
        return stock_name
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    try:
        r = requests.get(url, verify=False, timeout=10)
        data = r.json()
        for item in data:
            if str(item.get('公司簡稱')) == str(stock_name) or str(item.get('公司名稱', '')).startswith(str(stock_name)):
                return str(item.get('公司代號'))
    except Exception:
        pass
    return stock_name

def get_stock_data(stock_input: str):
    """取得現貨股價與歷史波動率"""
    stock_id = resolve_stock_id(stock_input)
    ticker = f"{stock_id}.TW"
    try:
        # 嘗試 .TW
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        if hist.empty:
            # 嘗試 .TWO (上櫃)
            ticker = f"{stock_id}.TWO"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
        if hist.empty or hist['Close'].dropna().empty:
            return None, None, None
            
        try:
            # 優先嘗試取得最即時報價 (支援盤中即時更新)
            current_price = float(stock.fast_info['lastPrice'])
        except:
            # 若無 latestPrice 則取歷史收盤最後一筆
            current_price = float(hist['Close'].dropna().iloc[-1])
            
        # 計算歷史波動率
        log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
        sigma = log_returns.std() * np.sqrt(252)
        if pd.isna(sigma) or sigma == 0:
            sigma = 0.3 # 預設 30% 波動率
            
        return current_price, sigma, hist[['Close']].dropna()
    except Exception as e:
        print(f"yfinance error: {e}")
        return None, None, None

def resolve_stock_name(stock_id: str) -> str:
    """如果輸入是代碼(如2330)，轉換為簡稱(如台積電)"""
    if not str(stock_id).isdigit():
        return stock_id
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    try:
        r = requests.get(url, verify=False, timeout=10)
        data = r.json()
        for item in data:
            if item.get('公司代號') == str(stock_id):
                return item.get('公司簡稱')
    except Exception:
        pass
    return stock_id

def fetch_all_warrants():
    """從 TWSE 取得所有上市權證基本資料"""
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap37_L"
    try:
        r = requests.get(url, timeout=15, verify=False)
        r.encoding = 'utf-8'
        data = r.json()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"fetch error: {e}")
        return pd.DataFrame()

def bs_delta(S, K, T, r, sigma, option_type):
    """計算 Black-Scholes Delta"""
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if option_type == 'C':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0

def process_and_score_warrants(df, stock_id, current_price, sigma):
    """過濾與評分權證"""
    # 解決代碼轉換名稱
    stock_name = resolve_stock_name(stock_id)
    # 篩選對應標的
    warrants = df[df['標的證券/指數'].astype(str).str.contains(stock_name, na=False)].copy()
    if warrants.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # 整理屬性
    today = pd.Timestamp(datetime.date.today())
    # 履約截止日格式有可能是民國年如 1150808 或含有空白
    def parse_tw_date(d_str):
        d_str = str(d_str).strip()
        if not d_str or len(d_str) < 6: return pd.NaT
        try:
            # 民國年轉換，如 1150808 -> 20260808
            if len(d_str) == 7: 
                d_str = str(int(d_str) + 19110000)
            return pd.to_datetime(d_str, format='%Y%m%d', errors='coerce')
        except:
            return pd.to_datetime(d_str, errors='coerce')
            
    warrants['到期日'] = warrants['履約截止日'].apply(parse_tw_date)
    warrants = warrants.dropna(subset=['到期日'])
    
    # 剩餘天數與年化時間
    warrants['剩餘天數'] = (warrants['到期日'] - today).dt.days
    warrants = warrants[warrants['剩餘天數'] > 0].copy() # 濾除已到期
    warrants['T_years'] = warrants['剩餘天數'] / 365.0
    
    warrants['履約價格'] = pd.to_numeric(warrants['最新履約價格(元)/履約指數'], errors='coerce')
    warrants = warrants.dropna(subset=['履約價格'])
    
    # 區分認購與認售 (權證類型 第一個字為 '認購' 或 '認售')
    warrants['類型'] = warrants['權證類型'].apply(lambda x: 'C' if '購' in str(x) else 'P')
    
    # 計算 Delta
    r = 0.015 # 假設無風險利率 1.5%
    warrants['Delta'] = warrants.apply(lambda row: bs_delta(current_price, row['履約價格'], row['T_years'], r, sigma, row['類型']), axis=1)
    
    # 計算價內外程度 (Moneyness)，單位為 %
    # 認購: (現貨 - 履約) / 履約 * 100
    # 認售: (履約 - 現貨) / 履約 * 100
    def calc_moneyness(row):
        if row['類型'] == 'C':
            return (current_price - row['履約價格']) / row['履約價格'] * 100
        else:
            return (row['履約價格'] - current_price) / row['履約價格'] * 100
            
    warrants['價內外(%)'] = warrants.apply(calc_moneyness, axis=1)
    
    # 建立全部的現有標的列表 fallback
    fallback_df = warrants[['權證代號', '權證簡稱', '類型', '到期日', '剩餘天數', '履約價格', '價內外(%)', 'Delta']].copy()
    fallback_df['價內外(%)'] = fallback_df['價內外(%)'].round(2)
    fallback_df['Delta'] = fallback_df['Delta'].round(4)
    fallback_df['到期日'] = fallback_df['到期日'].dt.strftime('%Y-%m-%d')
    fallback_df.sort_values(by='剩餘天數', ascending=False, inplace=True)
    
    # 硬性過濾條件：價外下限 -20% (即價內外 >= -20)
    filtered = warrants[warrants['價內外(%)'] >= -20.0].copy()
    
    if filtered.empty:
        return pd.DataFrame(), fallback_df
        
    # 評分機制 1~10 分
    # 1. 天數分數: 天數介於 90 ~ 180 天最佳 (3分), <30天最危險扣分, >180天尚可
    def score_days(days):
        if 90 <= days <= 180: return 3
        elif 60 <= days < 90: return 2
        elif days > 180: return 2
        elif 30 <= days < 60: return 1
        else: return 0 # 太短
        
    # 2. 價內外分數: 微價外到價內最佳 (Moneyness -5% ~ 10% 最佳)
    def score_moneyness(m):
        if -5 <= m <= 10: return 4
        elif -10 <= m < -5: return 3
        elif 10 < m <= 20: return 2 # 深度價內槓桿小
        elif -20 <= m < -10: return 1 # 較深價外
        else: return 1
        
    # 3. Delta分數: Delta絕對值愈接近 0.5 槓桿效應最佳 (或者Delta越大連動越好，這裡給偏好連動的)
    def score_delta(d):
        abs_d = abs(d)
        if 0.4 <= abs_d <= 0.7: return 3
        elif 0.2 <= abs_d < 0.4: return 2
        elif abs_d > 0.7: return 2
        else: return 1
        
    filtered['Score'] = (
        filtered['剩餘天數'].apply(score_days) + 
        filtered['價內外(%)'].apply(score_moneyness) + 
        filtered['Delta'].apply(score_delta)
    )
    # 取最高分10分
    filtered['推薦總分'] = filtered['Score'].clip(upper=10)
    
    final_df = filtered[['權證代號', '權證簡稱', '類型', '到期日', '剩餘天數', '履約價格', '價內外(%)', 'Delta', '推薦總分']].copy()
    final_df['價內外(%)'] = final_df['價內外(%)'].round(2)
    final_df['Delta'] = final_df['Delta'].round(4)
    final_df['到期日'] = final_df['到期日'].dt.strftime('%Y-%m-%d')
    
    # 降序排序
    final_df = final_df.sort_values(by=['推薦總分', '剩餘天數'], ascending=[False, False])
    
    return final_df.head(5), fallback_df

def bs_price(S, K, T, r, sigma, option_type):
    """計算 Black-Scholes 理論價格"""
    if T <= 0:
        return max(0.0, S - K) if option_type == 'C' else max(0.0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'C':
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def evaluate_single_warrant(df, warrant_code: str):
    """輸入權證代號，回傳該權證的理論數據與規格"""
    warrant_code = str(warrant_code).strip()
    warrant = df[df['權證代號'].astype(str).str.strip() == warrant_code].copy()
    if warrant.empty:
        return None, "⚠️ 在目前上市權證清單中找不到該代號，可能是已經下市、到期或是上櫃(OTC)權證。"
        
    row = warrant.iloc[0]
    stock_name = row['標的證券/指數']
    
    # 處理標的轉換為代碼並取得價格
    stock_id = resolve_stock_id(stock_name)
    current_price, sigma, _ = get_stock_data(stock_id)
    if current_price is None:
        return None, f"⚠️ 無法取得標的 [{stock_name}] 的現貨價格，無法進行試算評價。"
        
    # 計算時間資訊
    today = pd.Timestamp(datetime.date.today())
    d_str = str(row['履約截止日']).strip()
    try:
        if len(d_str) == 7: d_str = str(int(d_str) + 19110000)
        exp_date = pd.to_datetime(d_str, format='%Y%m%d', errors='coerce')
    except:
        exp_date = pd.to_datetime(d_str, errors='coerce')
        
    if pd.isna(exp_date):
        return None, "⚠️ 無法解析該權證的到期日。"
        
    days_left = (exp_date - today).days
    if days_left <= 0:
        return None, "⚠️ 該權證已到期。"
        
    T_years = days_left / 365.0
    r = 0.015
    strike = pd.to_numeric(row['最新履約價格(元)/履約指數'], errors='coerce')
    option_type = 'C' if '購' in str(row['權證類型']) else 'P'
    
    delta = bs_delta(current_price, strike, T_years, r, sigma, option_type)
    
    # 計算理論價格
    try:
        # 每仟單位權證可配發標的股數，如 100 代表行使比例為 100/1000 = 0.1
        exercise_qty_str = str(row['最新標的履約配發數量(每仟單位權證)']).replace(',', '')
        exercise_ratio = float(exercise_qty_str) / 1000.0
    except:
        exercise_ratio = 1.0 # 預設 1:1
        
    opt_price = bs_price(current_price, strike, T_years, r, sigma, option_type)
    theo_warrant_price = opt_price * exercise_ratio
    
    if option_type == 'C':
        moneyness = (current_price - strike) / strike * 100
    else:
        moneyness = (strike - current_price) / strike * 100
        
    info = {
        "權證代號": row['權證代號'],
        "權證簡稱": row['權證簡稱'],
        "標的": stock_name,
        "類型": "認購(Call)" if option_type == 'C' else "認售(Put)",
        "行使比例": exercise_ratio,
        "到期日": exp_date.strftime('%Y-%m-%d'),
        "剩餘天數": days_left,
        "現貨價": round(current_price, 2),
        "履約價": round(strike, 2),
        "價內外(%)": round(moneyness, 2),
        "Delta": round(delta, 4),
        "理論價格": round(theo_warrant_price, 4)
    }
    
    return info, "SUCCESS"
