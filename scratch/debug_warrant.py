import sys
sys.path.append(r"c:\Users\midst\OneDrive\桌面\youanalysis_notes\權證篩選器")
from warrant_engine import load_all_warrants
df = load_all_warrants()
w = df[df['w_code'] == '055547']
print(w)
