import streamlit as st
import warrant_engine
import importlib
importlib.reload(warrant_engine)
import pandas as pd

st.set_page_config(page_title="專業權證篩選器", page_icon="📈", layout="wide")

st.title("📈 專業權證篩選器 (Warrant Screener)")
st.markdown("""
提供全台上市權證即時分析！您可以利用「標的篩選」找出符合條件的最佳權證，或是利用「單一評價」診斷您手中的特定權證健康度。
""")

tab1, tab2 = st.tabs(["📊 標的權證篩選", "🎯 單點權證評價診斷"])

with tab1:
    st.markdown("### 輸入標的股票進行篩選")
    with st.form("search_form", border=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            stock_input = st.text_input("輸入股票代碼或名稱 (例: 2330 或 台積電)", value="2330")
        with col2:
            st.write("") # padding
            st.write("") 
            search_btn = st.form_submit_button("執行篩選", type="primary", use_container_width=True)
        
    st.markdown("---")
    
    if search_btn and stock_input:
        with st.spinner(f"正在爬取 {stock_input} 的即時股價與權證資料..."):
            # 1. 取得現貨股價
            price, sigma, hist = warrant_engine.get_stock_data(stock_input)
            
            if price is None:
                st.error(f"⚠️ 無法取得 {stock_input} 的股價資料，請確認代碼或名稱是否正確。")
            else:
                # 繪製左側線圖與右側大型報價板
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 📈 近三個月現貨日線圖")
                    st.line_chart(hist, height=250)
                with c2:
                    # 垂直置中與大型數字排版
                    st.write("")
                    st.write("")
                    st.markdown("#### 🎯 標的最新現貨價")
                    st.markdown(f"<h1 style='color: #FF4B4B; font-size: 5.5rem; margin-top: -15px; margin-bottom: 0px;'>{price:.2f} <span style='font-size: 2rem; color: #888;'>元</span></h1>", unsafe_allow_html=True)
                    st.info(f"📊 推測年化波動率： **{sigma*100:.2f}%**")
                    
                st.markdown("---")
                
                # 2. 獲取所有權證並初步處理
                all_warrants_df = warrant_engine.fetch_all_warrants()
                
                if all_warrants_df.empty:
                    st.error("⚠️ 無法連線至證交所取得權證名單，請稍後再試。")
                else:
                    # 3. 篩選與評分
                    recommended, fallback = warrant_engine.process_and_score_warrants(
                        all_warrants_df, stock_input, price, sigma
                    )
                    
                    # 若完全找不到這檔股票相關的權證
                    if fallback.empty:
                        st.warning(f"⚠️ 市場上目前沒有找到對應標的 ({stock_input}) 的任何上市權證。")
                    else:
                        if not recommended.empty:
                            st.subheader(f"🏆 Top 推薦清單 (最高推薦分前 {len(recommended)} 名)")
                            st.dataframe(
                                recommended,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "推薦總分": st.column_config.ProgressColumn(
                                        "推薦總分",
                                        help="1-10分，綜合考量 Delta, 價內外與天數",
                                        format="%f",
                                        min_value=0,
                                        max_value=10,
                                    ),
                                    "Delta": st.column_config.NumberColumn(format="%.4f"),
                                    "價內外(%)": st.column_config.NumberColumn(format="%.2f %%"),
                                }
                            )
                        else:
                            st.warning("⚠️ 沒有符合「價外 -20% 以上」與其他篩選條件的推薦權證。")
                            
                        with st.expander(f"📥 檢視市場上現有些標的所有權證 ({len(fallback)} 檔)"):
                            st.dataframe(fallback, use_container_width=True, hide_index=True)
                            
                        # 4. 風險與策略提示
                        st.markdown("---")
                        st.subheader("💡 系統風險與策略提醒")
                        st.info("""
    **最佳操作策略建議**：
    - **時間耗損 (Theta風險)**：若您選擇的權證剩餘天數低於 60 天，時間價值會呈現加速流失，建議作為「極短線」波段操作，不宜長抱。
    - **價外深度**：若因市場大幅震盪使得權證掉入價外 -20% 以外的區間，Delta 值將快速趨近於 0 (俗稱龜苓膏)，此時幾乎與現貨脫鉤，建議果斷停損或切換標的。
    - **因應變化**：請隨時注意現貨趨勢，當方向看錯時，權證的高槓桿會放大虧損。進場前務必設定停損價位，同時在選單中建議優先看「微價外」(-5%) 至「微價內」(+10%) 的標的，流動性與連動性較佳。
                        """)

with tab2:
    st.markdown("### 輸入單一權證代號進行健康度診斷")
    with st.form("eval_form", border=False):
        colA, colB = st.columns([3, 1])
        with colA:
            warrant_input = st.text_input("輸入要診斷的權證代號 (例: 030003)")
        with colB:
            st.write("")
            st.write("")
            eval_btn = st.form_submit_button("給予評價", type="secondary", use_container_width=True)
        
    st.markdown("---")
    
    if eval_btn and warrant_input:
        with st.spinner(f"正在系統中查詢 {warrant_input} 的各項資料與診斷..."):
            df = warrant_engine.fetch_all_warrants()
            if df.empty:
                st.error("連線錯誤")
            else:
                info, message = warrant_engine.evaluate_single_warrant(df, str(warrant_input).strip())
                if info is None:
                    st.error(message)
                else:
                    st.markdown(f"## 🎯 權證基本資訊： **{info['權證簡稱']} ({info['權證代號']})**")
                    st.markdown(f"**標的現貨**：{info['標的']} | **權證類型**：{info['類型']} | **到期日**：{info['到期日']} | **行使比例**：{info['行使比例']}")
                    
                    st.markdown("### 📊 核心數據指標")
                    
                    # 使用 metric 呈現
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("今日現貨收盤價", f"{info['現貨價']} 元")
                        st.metric("權證履約價", f"{info['履約價']} 元")
                    with m2:
                        st.metric("剩餘時間", f"{info['剩餘天數']} 天")
                        st.metric("Delta 值", f"{info['Delta']:.4f}")
                    with m3:
                        moneyness_val = info['價內外(%)']
                        sign = "+" if moneyness_val > 0 else ""
                        st.metric("價內外程度", f"{sign}{moneyness_val:.2f} %")
                        st.metric("B-S 理論價格", f"{info['理論價格']:.4f} 元", help="由 Black-Scholes 模型推算出的權證含行使比例理論價，僅供報價參考。")
