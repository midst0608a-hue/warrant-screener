import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants, get_stock_info, calculate_warrant_metrics

df_market = load_all_warrants()
stock_warrants = df_market[df_market['stock_id'] == "3105"]
price, sigma, sid = get_stock_info("3105")
df_scored = calculate_warrant_metrics(stock_warrants, price, sigma)
if not df_scored.empty:
    print(df_scored[['代號', '認購/售', '履約價', '價外程度(%)', '理論價']].head(20))
