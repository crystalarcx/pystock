import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import Dict, Any

# Configure Streamlit page
st.set_page_config(
    page_title="股票資料測試工具",
    page_icon="🧪",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
}
.hero-title {
    color: white;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    color: rgba(255,255,255,0.8);
    font-size: 1.2rem;
}
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

def get_taiwan_stock_info_enhanced(symbol: str) -> Dict[str, Any]:
    """獲取台股資訊 (增強版)"""
    # 嘗試不同的台股後綴
    suffixes_to_try = ['.TW', '.TWO']
    
    for suffix in suffixes_to_try:
        try:
            ticker_symbol = symbol + suffix
            ticker = yf.Ticker(ticker_symbol)
            
            # 獲取基本資訊
            info = ticker.info
            
            # 檢查是否有有效資料
            if not info or info.get('regularMarketPrice') is None:
                continue
                
            # 獲取股息歷史
            dividends = ticker.dividends
            actions = ticker.actions
            
            result = {
                'ticker_used': ticker_symbol,
                'quote_type': info.get('quoteType', 'Unknown'),
                'last_dividend_date': 'N/A',
                'last_dividend_amount': 0,
                'total_dividends_12m': 0,
                'last_split_date': 'N/A',
                'last_split_ratio': 'N/A',
                'data_quality': 'Unknown'
            }
            
            # 處理股息資料
            if not dividends.empty:
                dividends_12m = dividends[dividends.index >= (datetime.now() - timedelta(days=365))]
                
                result['last_dividend_date'] = dividends.index[-1].strftime('%Y-%m-%d')
                result['last_dividend_amount'] = float(dividends.iloc[-1])
                result['total_dividends_12m'] = float(dividends_12m.sum())
            
            # 處理股票分割資料
            if not actions.empty and 'Stock Splits' in actions.columns:
                splits = actions['Stock Splits'].dropna()
                if not splits.empty:
                    result['last_split_date'] = splits.index[-1].strftime('%Y-%m-%d')
                    result['last_split_ratio'] = f"1:{splits.iloc[-1]}"
            
            # 評估資料品質
            quality_score = 0
            quality_issues = []
            
            if info.get('regularMarketPrice'):
                quality_score += 1
            else:
                quality_issues.append("無市價資料")
                
            if not dividends.empty:
                quality_score += 2
            else:
                quality_issues.append("無股息資料")
                
            if info.get('longName') or info.get('shortName'):
                quality_score += 1
            else:
                quality_issues.append("無公司名稱")
            
            if quality_issues:
                result['data_quality'] = f"Score: {quality_score}/4, Issues: {', '.join(quality_issues)}"
            else:
                result['data_quality'] = f"Score: {quality_score}/4, Complete"
            
            return result
            
        except Exception as e:
            continue
    
    # 如果所有嘗試都失敗
    return {
        'ticker_used': f"{symbol}.TW (Failed)",
        'quote_type': 'Unknown',
        'last_dividend_date': 'N/A',
        'last_dividend_amount': 0,
        'total_dividends_12m': 0,
        'last_split_date': 'N/A',
        'last_split_ratio': 'N/A',
        'data_quality': 'Data retrieval failed'
    }

def get_stock_info(symbol: str, is_taiwan_stock: bool = False) -> Dict[str, Any]:
    """獲取股票資訊 (美股/海外股票)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 獲取股息歷史
        dividends = ticker.dividends
        actions = ticker.actions
        
        result = {
            'ticker_used': symbol,
            'quote_type': info.get('quoteType', 'Unknown'),
            'last_dividend_date': 'N/A',
            'last_dividend_amount': 0,
            'total_dividends_12m': 0,
            'last_split_date': 'N/A',
            'last_split_ratio': 'N/A',
            'data_quality': 'Unknown'
        }
        
        # 處理股息資料
        if not dividends.empty:
            dividends_12m = dividends[dividends.index >= (datetime.now() - timedelta(days=365))]
            
            result['last_dividend_date'] = dividends.index[-1].strftime('%Y-%m-%d')
            result['last_dividend_amount'] = float(dividends.iloc[-1])
            result['total_dividends_12m'] = float(dividends_12m.sum())
        
        # 處理股票分割資料
        if not actions.empty and 'Stock Splits' in actions.columns:
            splits = actions['Stock Splits'].dropna()
            if not splits.empty:
                result['last_split_date'] = splits.index[-1].strftime('%Y-%m-%d')
                result['last_split_ratio'] = f"1:{splits.iloc[-1]}"
        
        # 評估資料品質
        quality_score = 0
        quality_issues = []
        
        if info.get('regularMarketPrice'):
            quality_score += 1
        else:
            quality_issues.append("無市價資料")
            
        if not dividends.empty:
            quality_score += 2
        else:
            quality_issues.append("無股息資料")
            
        if info.get('longName') or info.get('shortName'):
            quality_score += 1
        else:
            quality_issues.append("無公司名稱")
        
        if quality_issues:
            result['data_quality'] = f"Score: {quality_score}/4, Issues: {', '.join(quality_issues)}"
        else:
            result['data_quality'] = f"Score: {quality_score}/4, Complete"
        
        return result
        
    except Exception as e:
        return {
            'ticker_used': f"{symbol} (Failed)",
            'quote_type': 'Unknown',
            'last_dividend_date': 'N/A',
            'last_dividend_amount': 0,
            'total_dividends_12m': 0,
            'last_split_date': 'N/A',
            'last_split_ratio': 'N/A',
            'data_quality': f'Error: {str(e)}'
        }

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
    
    selected_quick_test = None
    for i, symbol in enumerate(quick_test_symbols):
        with test_buttons_col[i]:
            if st.button(f"測試 {symbol}", key=f"test_{symbol}"):
                selected_quick_test = symbol
    
    # 如果點擊了快速測試按鈕，更新test_symbol
    if selected_quick_test:
        test_symbol = selected_quick_test
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
                        score = int(quality.split(': ')[1].split('/')[0])
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

def main():
    # 主標題
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">股票資料測試工具</h1>
        <p class="hero-subtitle">測試 yfinance 股息資料抓取功能</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 渲染測試工具
    render_stock_testing_tool()

if __name__ == "__main__":
    main()