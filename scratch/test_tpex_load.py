import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants

df = load_all_warrants()
if not df.empty:
    print("Total warrants:", len(df))
    print("Market counts:")
    print(df['market'].value_counts())
    
    # Try an OTC stock, say 6187, or 3105
    otc_warrants = df[df['market'] == '上櫃']
    num_otc = len(otc_warrants)
    print("Sample OTC warrants head:")
    if num_otc > 0:
        print(otc_warrants.head())
    else:
        print("NO OTC Warrants found!")
