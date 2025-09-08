import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re
import time
import yfinance as yf
import requests

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 簡化版CSS樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .main > div { padding-top: 1rem; }
    
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        margin: 1rem 0 0 0;
        opacity: 0.9;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        border: 1px solid rgba(0,0,0,0.05);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.8rem 0;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        font-weight: 500;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    .profit { color: #27ae60; background: rgba(39, 174, 96, 0.1); }
    .loss { color: #e74c3c; background: rgba(231, 76, 60, 0.1); }
    
    .trading-section {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border: 2px solid rgba(76, 175, 80, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .trading-title {
        color: #2e7d32;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets 配置
SHEET_CONFIGS = {
    'jason': {
        'id': '17qQIU4KMtbTpo_ozguuzKFHf1HHOhuEBanXxCyE8k4M',
        'holdings_range': '總覽與損益!A:I',
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'rita': {
        'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'ed': {
        'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'ed_overseas': {
        'schwab': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': 'schwab!A:Z'
        },
        'cathay': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': '總覽與損益!A:Z'
        },
        'fubon_uk': {
            'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
            'range': '總覽與損益!A:M'
        }
    }
}

# 目標配置設定
TARGET_ALLOCATION = {
    '美股ETF': 35,
    '美股個股': 20,
    '台股ETF': 20,
    '台股個股': 15,
    '美債ETF': 10
}

@st.cache_resource(ttl=3600)
def get_google_sheets_service():
    """取得Google Sheets服務實例"""
    try:
        if "gcp_service_account" in st.secrets:
            credentials_info = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(credentials_info)
        else:
            st.warning("找不到 gcp_service_account 設定，某些功能可能無法使用")
            return None
        
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets'
        ])
        
        return build('sheets', 'v4', credentials=scoped_credentials)
    except Exception as e:
        st.warning(f"Google Sheets API 設置失敗: {e}")
        return None

@st.cache_data(ttl=14400)
def get_usd_twd_rate():
    """取得USDTWD 匯率"""
    try:
        ticker = yf.Ticker("USDTWD=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return 31.0
    except Exception:
        return 31.0

@st.cache_data(ttl=3600)
def get_stock_name(stock_code):
    """查詢股票名稱"""
    try:
        # 簡化版本：如果無法連接API，返回預設名稱
        return f"股票{stock_code}"
    except Exception:
        return f"股票{stock_code}"

@st.cache_data
def parse_number(value):
    """解析數字，處理各種格式"""
    if pd.isna(value) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if not value or value == '':
        return 0.0
    
    cleaned = str(value).replace(',', '').replace('%', '').replace('"', '').replace('$', '').strip()
    
    if not cleaned:
        return 0.0
        
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def append_to_sheet(spreadsheet_id, range_name, values):
    """將一列資料附加到指定的 Google Sheet 中"""
    try:
        service = get_google_sheets_service()
        if not service:
            st.error("無法連接至 Google Sheets 服務")
            return False

        body = {
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"寫入 Google Sheets 失敗: {e}")
        return False

@st.cache_data(ttl=1800)
def load_sheet_data(person, data_type, broker=None):
    """從Google Sheets載入數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        if person == 'ed_overseas' and broker:
            config = SHEET_CONFIGS[person][broker]
            sheet_id = config['id']
            range_name = config['range']
        else:
            config = SHEET_CONFIGS.get(person, {})
            sheet_id = config.get('id')
            
            if data_type == 'holdings':
                range_name = config.get('holdings_range')
            elif data_type == 'dca':
                range_name = config.get('dca_range')
            elif data_type == 'trend':
                range_name = config.get('trend_range')
            else:
                return pd.DataFrame()
        
        if not range_name or not sheet_id:
            return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        
        # 簡化數據處理邏輯
        max_cols = len(values[0]) if values else 0
        normalized_values = [row + [''] * (max_cols - len(row)) for row in values]
        
        df = pd.DataFrame(normalized_values[1:], columns=normalized_values[0])
        df = df.dropna(how='all')
        
        return df
        
    except Exception as e:
        st.warning(f"載入{person} {broker or data_type}數據失敗: {str(e)}")
        return pd.DataFrame()

def render_trading_interface(person):
    """渲染交易記錄界面"""
    if person != 'rita':
        return
        
    st.markdown('<div class="trading-section">', unsafe_allow_html=True)
    st.markdown('<div class="trading-title">📝 新增交易記錄</div>', unsafe_allow_html=True)
    
    # 初始化session state
    if 'holding_type' not in st.session_state:
        st.session_state.holding_type = None
    if 'trade_type' not in st.session_state:
        st.session_state.trade_type = None
    
    # 第一組按鈕：持有類型
    st.write("**選擇持有類型：**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 原本持有", key="original_holding", use_container_width=True):
            st.session_state.holding_type = "original"
    
    with col2:
        if st.button("✨ 新持有", key="new_holding", use_container_width=True):
            st.session_state.holding_type = "new"
    
    if st.session_state.holding_type:
        st.success(f"已選擇：{'原本持有' if st.session_state.holding_type == 'original' else '新持有'}")
    
    # 第二組按鈕：交易類型
    st.write("**選擇交易類型：**")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("📈 買進", key="buy_trade", use_container_width=True):
            st.session_state.trade_type = "buy"
    
    with col4:
        if st.button("📉 賣出", key="sell_trade", use_container_width=True):
            st.session_state.trade_type = "sell"
    
    if st.session_state.trade_type:
        st.success(f"已選擇：{'買進' if st.session_state.trade_type == 'buy' else '賣出'}")
    
    # 只有當兩個選項都選擇後才顯示輸入表單
    if st.session_state.holding_type and st.session_state.trade_type:
        st.write("---")
        
        with st.form("trading_form", clear_on_submit=True):
            st.write("**交易詳情：**")
            
            col5, col6, col7 = st.columns(3)
            
            with col5:
                trade_date = st.date_input("交易日期", value=datetime.now())
            
            with col6:
                stock_code = st.text_input("股票代號", placeholder="例如：2330")
            
            with col7:
                stock_price = st.number_input(
                    f"{'買入股價' if st.session_state.trade_type == 'buy' else '賣出股價'}", 
                    min_value=0.0, 
                    format="%.2f",
                    step=0.1
                )
            
            col8, col9 = st.columns(2)
            
            with col8:
                stock_quantity = st.selectbox(
                    "股數",
                    options=[1000, 2000, 3000, 4000, 5000, 10000, 15000, 20000],
                    index=0
                )
            
            with col9:
                st.write("")
                st.write("")
                submit_button = st.form_submit_button(
                    f"確認{('買進' if st.session_state.trade_type == 'buy' else '賣出')}",
                    use_container_width=True
                )
            
            if submit_button:
                if not stock_code or stock_price <= 0:
                    st.error("請填寫完整的股票代號和股價！")
                else:
                    # 執行交易記錄
                    success = execute_trade_record(
                        person, trade_date, stock_code, stock_price, 
                        stock_quantity, st.session_state.trade_type, 
                        st.session_state.holding_type
                    )
                    
                    if success:
                        st.success("交易記錄已成功新增！")
                        # 清空session state
                        st.session_state.holding_type = None
                        st.session_state.trade_type = None
                        # 清除快取並重新載入
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("交易記錄新增失敗，請稍後重試。")
    
    st.markdown('</div>', unsafe_allow_html=True)

def execute_trade_record(person, trade_date, stock_code, stock_price, stock_quantity, trade_type, holding_type):
    """執行交易記錄寫入"""
    try:
        # 準備交易記錄數據
        date_str = trade_date.strftime('%Y/%m/%d')
        
        if trade_type == "buy":
            actual_quantity = stock_quantity
            total_cost = stock_price * stock_quantity
        else:  # sell
            actual_quantity = -stock_quantity
            total_cost = -(stock_price * stock_quantity)
        
        # 交易記錄資料
        trade_record = [date_str, stock_code, stock_price, "", "", total_cost, actual_quantity]
        
        # 寫入交易記錄到 Google Sheets
        sheet_id = SHEET_CONFIGS[person]['id']
        trade_success = append_to_sheet(sheet_id, '交易紀錄', [trade_record])
        
        if not trade_success:
            return False
        
        # 如果是新持有，還需要寫入總覽與損益表
        if holding_type == "new":
            stock_name = get_stock_name(stock_code)
            holding_record = [stock_code, stock_name]
            
            holding_success = append_to_sheet(sheet_id, '總覽與損益', [holding_record])
            return holding_success
        
        return True
        
    except Exception as e:
        st.error(f"執行交易記錄失敗: {e}")
        return False

def render_user_selection():
    """渲染使用者選擇按鈕"""
    user_options = [
        {'key': 'jason', 'icon': '👨‍💼', 'label': 'Jason', 'desc': '台股投資'},
        {'key': 'rita', 'icon': '👩‍💼', 'label': 'Rita', 'desc': '台股投資'},
        {'key': 'ed', 'icon': '👨‍💻', 'label': 'Ed', 'desc': '台股投資'},
        {'key': 'ed_overseas', 'icon': '🌐', 'label': 'Ed', 'desc': '海外總覽'},
        {'key': 'asset_allocation', 'icon': '📊', 'label': '資產配置', 'desc': '整體配置'}
    ]
    
    cols = st.columns(len(user_options))
    
    if 'selected_person' not in st.session_state:
        st.session_state.selected_person = 'jason'
    
    for i, option in enumerate(user_options):
        with cols[i]:
            if st.button(
                f"{option['icon']}\n{option['label']}\n{option['desc']}", 
                key=f"btn_{option['key']}",
                use_container_width=True
            ):
                st.session_state.selected_person = option['key']
    
    return st.session_state.selected_person

def render_summary_cards(person, holdings_df, dca_df=None):
    """渲染摘要卡片"""
    if person in ['ed_overseas', 'asset_allocation']:
        return
    
    try:
        required_columns = ['總投入成本', '目前總市值', '未實現損益']
        if not all(col in holdings_df.columns for col in required_columns) or holdings_df.empty:
            st.warning("持股數據不完整或為空")
            return
        
        # 確保數值欄位為數字格式
        for col in required_columns:
            holdings_df[col] = holdings_df[col].apply(parse_number)
        
        total_cost = holdings_df['總投入成本'].sum()
        total_value = holdings_df['目前總市值'].sum()
        total_pl = holdings_df['未實現損益'].sum()
        total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">總投入成本</div><div class="metric-value">NT${total_cost:,.0f}</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">目前市值</div><div class="metric-value">NT${total_value:,.0f}</div></div>', unsafe_allow_html=True)
        
        with col3:
            profit_class = 'profit' if total_pl >= 0 else 'loss'
            st.markdown(f'<div class="metric-card"><div class="metric-label">未實現損益</div><div class="metric-value {profit_class}">NT${total_pl:,.0f}</div><div class="metric-change {profit_class}">{total_return:+.2f}%</div></div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card"><div class="metric-label">定期定額</div><div class="metric-value">設定中</div></div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"摘要卡片渲染錯誤: {str(e)}")

def main():
    """主要應用程式邏輯"""
    
    st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
    
    person = render_user_selection()
    
    # 更新按鈕
    col1, col2, col3 = st.columns([1, 1, 8])
    with col2:
        if st.button('🔄 更新', key='refresh_button', help='清除快取並重新載入數據'):
            st.cache_data.clear()
            st.rerun()

    # 根據選擇的人員載入對應頁面
    if person == 'asset_allocation':
        st.header("📊 整體資產配置分析")
        st.info("資產配置功能開發中...")
        
    elif person == 'ed_overseas':
        st.header("Ed 海外投資總覽") 
        st.info("海外投資功能開發中...")
        
    else:
        st.header(f"{person.capitalize()} 台股投資總覽")
        
        # 載入數據
        with st.spinner(f'載入 {person} 的投資數據...'):
            holdings_df = load_sheet_data(person, 'holdings')
        
        if not holdings_df.empty:
            render_summary_cards(person, holdings_df)
            
            # Rita 專屬交易記錄功能
            if person == 'rita':
                render_trading_interface(person)
            
            # 顯示持股資料
            st.subheader("持股明細")
            st.dataframe(holdings_df, use_container_width=True)
            
        else:
            st.warning(f"無法載入 {person} 的投資數據，或數據為空")
            if person == 'rita':
                render_trading_interface(person)

if __name__ == "__main__":
    main()
