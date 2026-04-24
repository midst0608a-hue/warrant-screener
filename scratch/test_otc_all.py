import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants, get_stock_info, calculate_warrant_metrics, get_low_liquidity_warrants

df_market = load_all_warrants()
for stock_input in ['6187', '3105', '8069', '3293']:
    stock_warrants = df_market[df_market['stock_id'] == stock_input]
    print(f"=== {stock_input} ===")
    print("Warrants before:", len(stock_warrants))
    
    # Do we get the price?
    price, sigma, sid = get_stock_info(stock_input)
    print("Price:", price)
