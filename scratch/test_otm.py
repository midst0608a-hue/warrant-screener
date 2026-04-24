import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants, get_stock_info, calculate_warrant_metrics

df_market = load_all_warrants()
stock_input = "6187"
stock_warrants = df_market[df_market['stock_id'] == stock_input]
price, sigma, sid = get_stock_info(stock_input)
df_scored = calculate_warrant_metrics(stock_warrants, price, sigma)
print(df_scored[['代號', '履約價', '價外程度(%)', '理論價']].head(10))
