import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import warrant_engine

def main():
    print("開始抓取全市場權證資料...")
    # 強制從線上抓取最新資料
    df = warrant_engine.load_all_warrants(force_fetch=True)
    
    if not df.empty and len(df) > 30000:
        twse_c = len(df[df['market'] == '上市'])
        tpex_c = len(df[df['market'] == '上櫃'])
        print(f"資料校驗通過：上市 {twse_c} 筆，上櫃 {tpex_c} 筆。")
        
        # 轉換為 dictionary list 並存成 JSON
        records = df.to_dict(orient="records")
        with open("warrants_data.json", "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"[完成] 成功抓取並儲存全市場共 {len(df)} 筆權證資料至 warrants_data.json！")
    else:
        print(f"[警告] 抓取資料異常 (筆數僅 {len(df)})，為防止資料被清空，已放棄寫入檔案，保留原現有資料。")

if __name__ == "__main__":
    main()
