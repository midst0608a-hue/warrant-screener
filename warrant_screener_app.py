import streamlit as st
import warrant_engine
import importlib
import datetime
import pandas as pd

importlib.reload(warrant_engine)

st.set_page_config(page_title="專業權證診斷器", layout="wide")
st.title("📈 專業權證全市場診斷器 (API版)")

# --- 載入全域資料庫快取 ---
@st.cache_data(ttl=3600)
def get_cached_warrants_v2():
    return warrant_engine.load_all_warrants()

try:
    df_market = get_cached_warrants_v2()
except Exception as e:
    st.error(f"資料庫戴入失敗：{e}")
    df_market = pd.DataFrame()

tab1, tab2 = st.tabs(["🔎 標的篩選推薦", "🎯 權證單點診斷"])

# --- 功能一：篩選推薦 ---
with tab1:
    st.subheader("1. 根據標的搜尋權證 (評分排行榜)")
    
    with st.form("search_form"):
        stock_input = st.text_input("輸入股票代號 (例: 2330, 6187)", value="2330")
        search_btn = st.form_submit_button("搜尋高分排行榜 (支援 Enter)", type="primary", use_container_width=True)
    
    if search_btn and not df_market.empty:
        with st.spinner("計算綜合評分中..."):
            stock_input_str = str(stock_input).strip()
            # 支援輸入數字代碼或中文名稱 (透過權證簡稱反查)
            stock_warrants = df_market[
                (df_market['stock_id'] == stock_input_str) | 
                (df_market['w_name'].str.contains(stock_input_str, na=False))
            ]
            
            if stock_warrants.empty:
                st.warning("找不到該標的的相關權證，請確認代號或名稱是否正確。")
            else:
                # 若使用者輸入中文名稱，自動從配對到的權證中取出正確的標的數字代號
                actual_sid = stock_warrants['stock_id'].iloc[0]
                price, sigma, sid = warrant_engine.get_stock_info(actual_sid)
                
                if price is None:
                    st.error(f"無法取得該標的 ({actual_sid}) 的最新報價，可能非有效上市櫃代號或網路不穩。")
                else:
                    is_disposal, disposal_msg = warrant_engine.check_disposal_status(actual_sid)
                    if is_disposal:
                        st.warning(f"⚠️ {disposal_msg} (資料來源：chengwaye.com)")
                    
                    # 顯示實際找到的標的代號
                    display_name = stock_input_str if not stock_input_str.isdigit() else actual_sid
                    st.markdown(f"### 📍 標的 **{display_name} ({actual_sid})** 最新現貨價格：**{round(price, 2)}** 元")
                    df_scored = warrant_engine.calculate_warrant_metrics(stock_warrants, price, sigma)
                    
                    if not df_scored.empty:
                        # 取得並排除造市專戶庫存不足之權證 (流動性極差的黑名單)
                        bad_warrants = warrant_engine.get_low_liquidity_warrants()
                        if bad_warrants:
                            df_scored = df_scored[~df_scored['代號'].astype(str).isin(bad_warrants)]
                        
                        if not df_scored.empty:
                            st.write(f"🔍 篩選結果：共找到 {len(df_scored)} 檔有效權證 (已排除庫存不足之極端標的，全數列出並依推薦分排序)：")
                            
                            # 重新排列欄位，強調關鍵參數 (往左集中)，包含價內程度
                            cols = ['代號', '名稱', '履約價', '價內程度(%)', '理論價', '剩餘天數', '實質槓桿', '綜合評分', '認購/售', '市場', '行使比例']
                            df_display = df_scored[cols]
                            
                            def highlight_score(val):
                                color = '#2E8B57' if val > 70 else ('#DAA520' if val > 40 else '#CD5C5C')
                                return f'background-color: {color}; color: white'
                            
                            st.dataframe(
                                df_display.style.map(highlight_score, subset=['綜合評分']), 
                                use_container_width=True, 
                                hide_index=True
                            )
                        else:
                            st.warning("目前無符合任何有效分數計算條件的權證。")
                    else:
                        st.warning("未能計算出有效評分。")


# --- 功能二：單點診斷 ---
with tab2:
    st.subheader("2. 權證單點財務指標診斷")
    
    # 不再需要區分上市/上櫃，直接查表最快
    with st.form("diag_form"):
        w_input = st.text_input("輸入權證代號 (例: 030573 或 70006C)", value="")
        diag_btn = st.form_submit_button("執行診斷 (支援 Enter)", type="primary", use_container_width=True)
    
    if diag_btn and w_input and not df_market.empty:
        with st.spinner("診斷資料與指標分析中..."):
            target_w = df_market[df_market['w_code'] == w_input.strip()]
            
            if target_w.empty:
                st.error(f"在全市場資料中找不到權證：{w_input}，請確認代號。")
            else:
                w_row = target_w.iloc[0]
                stock_id = w_row['stock_id']
                market_mode = w_row['market']
                
                price, sigma, sid = warrant_engine.get_stock_info(stock_id)
                
                if price:
                    df_scored = warrant_engine.calculate_warrant_metrics(target_w, price, sigma)
                    if not df_scored.empty:
                        res = df_scored.iloc[0]
                        
                        st.success(f"✅ {market_mode} 資料庫獲取成功：{res['名稱']} ({res['代號']})")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("標的現貨價", f"{round(price, 2)} 元")
                        c2.metric("BS 理論價", f"{res['理論價']} 元")
                        c3.metric("實質槓桿", f"{res['實質槓桿']} 倍")
                        
                        st.divider()
                        st.write(f"**詳細串接與評分參數：**")
                        col_a, col_b = st.columns(2)
                        col_a.write(f"- **標的代號**：{stock_id}")
                        col_a.write(f"- **履約價格**：{res['履約價']}")
                        col_a.write(f"- **行使比例**：{res['行使比例']}")
                        col_a.write(f"- **認購/認售**：{res['認購/售']}")
                        
                        col_b.write(f"- **剩餘天數**：{res['剩餘天數']} 天")
                        col_b.write(f"- **權證價內程度**：{res['價內程度(%)']}%")
                        col_b.write(f"- **系統綜合評分**：{res['綜合評分']} 分")
                        
                        # 外部連結按鈕
                        target_url = f"https://www.twse.com.tw/zh/products/securities/warrant/infomation/stock.html" if market_mode=="上市" else f"https://www.tpex.org.tw/zh-tw/derivative/warrant/info/search.html"
                        st.link_button(f"🔗 前往 {market_mode} 官方網頁查看原始資料", target_url, use_container_width=True)
                else:
                    st.error("無法取得該標的之歷史股價以進行運算。")