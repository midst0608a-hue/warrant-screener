import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants, get_stock_info, calculate_warrant_metrics, get_low_liquidity_warrants

df_market = load_all_warrants()
stock_input = "6187"
stock_warrants = df_market[df_market['stock_id'] == stock_input]
print(f"Total Warrants for {stock_input}:", len(stock_warrants))

price, sigma, sid = get_stock_info(stock_input)
print(f"Price: {price}, Sigma: {sigma}")

if not stock_warrants.empty and price is not None:
    df_scored = calculate_warrant_metrics(stock_warrants, price, sigma)
    print("Scored warrants:", len(df_scored))
    
    bad_warrants = get_low_liquidity_warrants()
    if bad_warrants:
        df_scored = df_scored[~df_scored['代號'].isin(bad_warrants)]
    print("After bad drop:", len(df_scored))
    
    df_filtered = df_scored[
        (df_scored['價外程度(%)'] >= -5.0) & 
        (df_scored['價外程度(%)'] <= 15.0)
    ]
    print("After filter:", len(df_filtered))
