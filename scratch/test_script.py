import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
import warrant_engine

print("--- Testing OTC ---")
otc_res = warrant_engine.get_otc_spec("700682")
print("OTC Spec: ", otc_res)

print("--- Testing Listed ---")
listed_res = warrant_engine.get_listed_spec("030573")
print("Listed Spec: ", listed_res)

print("--- Testing Stock Info ---")
p, sig, s_id = warrant_engine.get_stock_info("2330")
print("Stock info 2330: ", p, sig, s_id)
