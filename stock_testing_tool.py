# 將這個新的 tab 加入到你的主程式的 main() 函數中

def render_stock_testing_tool():
    """股票資料測試工具"""
    st.markdown("## 股票資料測試工具")
    st.markdown("輸入股票代號來測試 yfinance 股息資料的抓取結果")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 輸入股票代號
        test_symbol = st.text_input(
            "輸入股票代號",
            placeholder="例如: 0056, 2330, AAPL",
            help="台股請輸入代號 (如 0056, 2330)，美股請輸入符號 (如 AAPL, TSLA)"
        )
    
    with col2:
        # 選擇股票類型
        stock_type = st.selectbox(
            "股票類型",
            ["台股", "美股/海外"]
        )
    
    # 預設測試股票按鈕
    st.markdown("**快速測試常見台股ETF:**")
    test_buttons_col = st.columns(5)
    quick_test_symbols = ['0056', '00878', '00713', '2881', '2882']
    
    for i, symbol in enumerate(quick_test_symbols):
        with test_buttons_col[i]:
            if st.button(f"測試 {symbol}", key=f"test_{symbol}"):
                test_symbol = symbol
                stock_type = "台股"
    
    if test_symbol and test_symbol.strip():
        st.markdown(f"### 測試結果: {test_symbol}")
        
        with st.spinner(f"正在測試 {test_symbol}..."):
            # 根據選擇的類型決定是否為台股
            is_taiwan = (stock_type == "台股")
            
            if is_taiwan:
                result = get_taiwan_stock_info_enhanced(test_symbol.strip())
            else:
                result = get_stock_info(test_symbol.strip(), is_taiwan_stock=False)
            
            # 顯示詳細結果
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 基本資訊")
                st.write(f"**原始代號:** {test_symbol}")
                st.write(f"**使用代號:** {result['ticker_used']}")
                st.write(f"**股票類型:** {result['quote_type']}")
                if 'data_quality' in result:
                    quality = result['data_quality']
                    if 'Score:' in quality:
                        score = int(quality.split(': ')[1])
                        color = "🟢" if score >= 3 else "🟡" if score >= 1 else "🔴"
                        st.write(f"**資料品質:** {color} {quality}")
                    else:
                        st.write(f"**資料品質:** 🔴 {quality}")
            
            with col2:
                st.markdown("#### 股息資訊")
                if result['last_dividend_date'] != 'N/A':
                    st.write(f"**最近配息日期:** {result['last_dividend_date']}")
                    currency = "USD" if not is_taiwan else "TWD"
                    if is_taiwan:
                        st.write(f"**最近配息金額:** NT${result['last_dividend_amount']:.2f}")
                        st.write(f"**12月配息總額:** NT${result['total_dividends_12m']:.2f}")
                    else:
                        st.write(f"**最近配息金額:** ${result['last_dividend_amount']:.4f}")
                        st.write(f"**12月配息總額:** ${result['total_dividends_12m']:.4f}")
                else:
                    st.warning("未找到股息資料")
                
                st.markdown("#### 分割資訊")
                if result['last_split_date'] != 'N/A':
                    st.write(f"**最近分割日期:** {result['last_split_date']}")
                    st.write(f"**分割比例:** {result['last_split_ratio']}")
                else:
                    st.info("近期無股票分割")
        
        # 顯示原始資料 (可折疊)
        with st.expander("查看原始回傳資料"):
            st.json(result)
        
        # 提供建議
        st.markdown("#### 建議與說明")
        if result['last_dividend_date'] == 'N/A':
            st.warning("""
            **未找到股息資料的可能原因:**
            1. 該股票/ETF 確實沒有配息紀錄
            2. yfinance 對該股票的資料支援度不佳
            3. 股票代號格式問題 (.TW vs .TWO)
            4. 資料更新延遲
            
            **建議:**
            - 確認該股票在 Yahoo Finance 網站上是否有股息資料
            - 嘗試不同的股票代號格式
            - 有些ETF可能配息頻率較低或為季配息
            """)
        else:
            st.success("成功獲取股息資料！資料可用於投資分析。")

# 更新後的 main() 函數 - 加入測試工具 tab
def main():
    # 主標題
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">投資總覽</h1>
        <p class="hero-subtitle">Jason • Rita • Ed • 富邦英股</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 分頁標籤 - 加入測試工具
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚘 Jason定期定額", 
        "👩🏻 Rita定期定額", 
        "👨🏻 Ed定期定額", 
        "🇬🇧 富邦英股總覽",
        "🧪 股票測試工具"  # 新增的測試工具 tab
    ])
    
    # 原有的 tabs 保持不變...
    with tab1:
        st.markdown("## Jason 定期定額投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="jason_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Jason投資數據..."):
            holdings_df = load_sheet_data('jason', 'holdings')
            dca_df = load_sheet_data('jason', 'dca')
            trend_df = load_sheet_data('jason', 'trend')
        
        if not holdings_df.empty:
            render_summary_cards('jason', holdings_df, dca_df)
            
            if not trend_df.empty:
                render_trend_chart('jason', trend_df)
            
            render_charts('jason', holdings_df)
            render_holdings_table('jason', holdings_df)
        else:
            st.error("無法載入Jason的投資數據，請檢查Google Sheets連接")
    
    with tab2:
        st.markdown("## Rita 定期定額投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="rita_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Rita投資數據..."):
            holdings_df = load_sheet_data('rita', 'holdings')
            dca_df = load_sheet_data('rita', 'dca')
            trend_df = load_sheet_data('rita', 'trend')
        
        if not holdings_df.empty:
            render_summary_cards('rita', holdings_df, dca_df)
            
            if not trend_df.empty:
                render_trend_chart('rita', trend_df)
            
            render_charts('rita', holdings_df)
            render_holdings_table('rita', holdings_df)
        else:
            st.error("無法載入Rita的投資數據，請檢查Google Sheets連接")
    
    with tab3:
        st.markdown("## Ed 定期定額投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="ed_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Ed投資數據..."):
            holdings_df = load_sheet_data('ed', 'holdings')
            dca_df = load_sheet_data('ed', 'dca')
            trend_df = load_sheet_data('ed', 'trend')
        
        if not holdings_df.empty:
            render_summary_cards('ed', holdings_df, dca_df)
            
            if not trend_df.empty:
                render_trend_chart('ed', trend_df)
            
            render_charts('ed', holdings_df)
            render_holdings_table('ed', holdings_df)
        else:
            st.warning("Ed的Google Sheets ID尚未設定，或無法載入投資數據")
    
    with tab4:
        st.markdown("## 富邦英股 海外投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="os_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入海外投資數據..."):
            holdings_df = load_sheet_data('os', 'holdings')
        
        if not holdings_df.empty:
            render_summary_cards('os', holdings_df)
            render_charts('os', holdings_df)
            render_holdings_table('os', holdings_df)
        else:
            st.error("無法載入海外投資數據，請檢查Google Sheets連接")
    
    with tab5:
        # 新增的股票測試工具
        render_stock_testing_tool()

if __name__ == "__main__":
    main()