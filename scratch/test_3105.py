import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants, get_stock_info, calculate_warrant_metrics

df_market = load_all_warrants()
stock_input = "3105"
stock_warrants = df_market[df_market['stock_id'] == stock_input]
price, sigma, sid = get_stock_info(stock_input)

df_scored = calculate_warrant_metrics(stock_warrants, price, sigma)
if not df_scored.empty:
    df_filtered = df_scored[
        (df_scored['價外程度(%)'] >= -5.0) & 
        (df_scored['價外程度(%)'] <= 15.0)
    ]
    print(f"3105 scored: {len(df_scored)}, filtered: {len(df_filtered)}")
else:
    print("3105 empty scored")
