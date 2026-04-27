import warrant_engine
import json

def main():
    print("開始抓取全市場權證資料...")
    # 強制從線上抓取最新資料
    df = warrant_engine.load_all_warrants(force_fetch=True)
    
    if not df.empty:
        # 轉換為 dictionary list 並存成 JSON
        records = df.to_dict(orient="records")
        with open("warrants_data.json", "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"成功抓取並儲存 {len(df)} 筆權證資料至 warrants_data.json！")
    else:
        print("抓取失敗，資料為空。")

if __name__ == "__main__":
    main()
