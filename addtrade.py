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

# 精簡版CSS樣式 - 移除未使用的動畫和複雜效果
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .main > div { padding-top: 1rem; }
    .css-1d391kg { display: none; }
    
    /* 簡化主標題區域 */
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
    
    /* 簡化用戶選擇按鈕 */
    .user-selection-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        margin: 1.5rem 0;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
    }
    
    .user-btn {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        color: #2c3e50;
        border: 2px solid rgba(52, 152, 219, 0.2);
        border-radius: 12px;
        padding: 16px 24px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 130px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .user-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(52, 152, 219, 0.2);
        border-color: #3498db;
    }
    
    .user-btn.active {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border-color: #3498db;
    }
    
    /* 簡化標籤頁 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: rgba(248, 249, 250, 0.8);
        padding: 6px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        padding: 12px 24px;
        color: #6c757d;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3498db, #2980b9) !important;
        color: white !important;
    }
    
    /* 簡化指標卡片 */
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
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c, #f39c12);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
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
    
    .metric-change {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 16px;
        display: inline-block;
    }
    
    .profit { color: #27ae60; background: rgba(39, 174, 96, 0.1); }
    .loss { color: #e74c3c; background: rgba(231, 76, 60, 0.1); }
    
    /* 簡化專用卡片 */
    .dca-card, .schwab-card, .cathay-card, .fubon-card, .allocation-card {
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .dca-card { background: linear-gradient(135deg, #f39c12, #e67e22); }
    .schwab-card { background: linear-gradient(135deg, #1f4e79, #2e6da4); }
    .cathay-card { background: linear-gradient(135deg, #8b0000, #dc143c); }
    .fubon-card { background: linear-gradient(135deg, #2d3436, #636e72); }
    .allocation-card { background: linear-gradient(135deg, #6c5ce7, #a29bfe); }
    
    .dca-item {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    
    /* 圖表容器 */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.4rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    
    /* 新增交易記錄區域樣式 */
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
    
    .button-group {
        display: flex;
        gap: 10px;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .trade-button {
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .trade-button.buy {
        background: linear-gradient(135deg, #27ae60, #229954);
        color: white;
    }
    
    .trade-button.sell {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
    }
    
    .trade-button:hover {
        transform: translateY(-2px);
    }
    
    /* 響應式 */
    @media (max-width: 768px) {
        .hero-title { font-size: 1.8rem; }
        .hero-section { padding: 1.5rem 1rem; }
        .metric-card { padding: 1.2rem; }
        .user-btn { min-width: 180px; }
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

# 優化1: 擴展快取設置
@st.cache_resource(ttl=3600)
def get_google_sheets_service():
    """取得Google Sheets服務實例"""
    try:
        if "gcp_service_account" in st.secrets:
            credentials_info = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(credentials_info)
        else:
            st.error("找不到 gcp_service_account 設定在 Streamlit secrets 中")
            return None
        
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets'
        ])
        
        return build('sheets', 'v4', credentials=scoped_credentials)
    except Exception as e:
        st.error(f"Google Sheets API 設置失敗: {e}")
        return None

# 優化2: 延長匯率快取時間到4小時
@st.cache_data(ttl=14400)
def get_usd_twd_rate():
    """取得USDTWD 匯率 - 延長快取時間"""
    try:
        ticker = yf.Ticker("USDTWD=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return 31.0
    except Exception as e:
        # 使用備用靜態匯率，減少API依賴
        return 31.0

# 新增: 股票名稱查詢函數
@st.cache_data(ttl=3600)
def get_stock_name(stock_code):
    """查詢股票名稱 - 使用台灣證券交易所API"""
    try:
        # 使用證交所API查詢股票資訊
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=20240101&stockNo={stock_code}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'title' in data:
                # 從title中提取股票名稱
                title = data['title']
                if stock_code in title:
                    name_part = title.split(stock_code)[-1].strip()
                    # 移除多餘的文字和符號
                    name = name_part.replace('每日收盤價', '').replace('各種統計資訊', '').strip()
                    if name:
                        return name
        
        # 如果API失敗，回傳預設值
        return f"股票{stock_code}"
    except Exception as e:
        return f"股票{stock_code}"

# 優化3: 為常用函數添加快取
@st.cache_data
def parse_number(value):
    """解析數字，處理各種格式 - 加入快取"""
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
    """將一列資料附加到指定的 Google Sheet 中。"""
    try:
        service = get_google_sheets_service()
        if not service:
            st.error("無法連接至 Google Sheets 服務。")
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

# 優化4: 延長數據快取時間到30分鐘
@st.cache_data(ttl=1800)
def load_sheet_data(person, data_type, broker=None):
    """從Google Sheets載入數據 - 延長快取時間"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        if person == 'ed_overseas':
            config = SHEET_CONFIGS[person][broker]
            sheet_id = config['id']
            range_name = config['range']
        else:
            config = SHEET_CONFIGS[person]
            sheet_id = config['id']
            
            if data_type == 'holdings':
                range_name = config['holdings_range']
            elif data_type == 'dca':
                range_name = config.get('dca_range')
            elif data_type == 'trend':
                range_name = config.get('trend_range')
            else:
                return pd.DataFrame()
        
        if not range_name:
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
        
        # 簡化數字欄位處理
        if person == 'ed_overseas':
            numeric_columns = [col for col in df.columns if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率'])]
        elif data_type == 'holdings':
            numeric_columns = ['總投入成本', '總持有股數', '目前股價', '目前總市值', '未實現損益', '報酬率']
        elif data_type == 'dca':
            numeric_columns = ['每月投入金額', '扣款日', '券商折扣']
        elif data_type == 'trend':
            numeric_columns = ['總市值']
        else:
            numeric_columns = []
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_number)
        
        return df
        
    except Exception as e:
        st.error(f"載入{person} {broker or data_type}數據失敗: {str(e)}")
        return pd.DataFrame()

# 優化5: 批次載入相關數據
@st.cache_data(ttl=1800)
def load_person_all_data(person):
    """批次載入單一用戶的所有數據"""
    if person == 'ed_overseas':
        return {
            'schwab': load_sheet_data('ed_overseas', None, 'schwab'),
            'cathay': load_sheet_data('ed_overseas', None, 'cathay'),
            'fubon_uk': load_sheet_data('ed_overseas', None, 'fubon_uk')
        }
    else:
        return {
            'holdings': load_sheet_data(person, 'holdings'),
            'dca': load_sheet_data(person, 'dca'),
            'trend': load_sheet_data(person, 'trend')
        }

def get_schwab_total_value(schwab_df):
    """從schwab工作表的B欄取得最下方的總市值數據"""
    try:
        if schwab_df.empty or len(schwab_df.columns) < 2:
            return 0.0
        
        b_column = schwab_df.iloc[:, 1]
        
        for i in range(len(b_column) - 1, -1, -1):
            value = b_column.iloc[i]
            if pd.notna(value) and str(value).strip() != '':
                parsed_value = parse_number(value)
                if parsed_value > 0:
                    return parsed_value
        
        return 0.0
    except Exception as e:
        st.error(f"解析嘉信證券總市值失敗: {e}")
        return 0.0

def get_cathay_total_value(cathay_df):
    """從總覽與損益工作表的F欄計算總市值"""
    try:
        if cathay_df.empty or len(cathay_df.columns) < 6:
            return 0.0
        
        f_column = cathay_df.iloc[:, 5]
        
        total = 0.0
        for value in f_column:
            if pd.notna(value) and str(value).strip() != '':
                parsed_value = parse_number(value)
                if parsed_value > 0:
                    total += parsed_value
        
        return total
    except Exception as e:
        st.error(f"計算國泰證券總市值失敗: {e}")
        return 0.0

def get_fubon_uk_total_value(fubon_df):
    """計算富邦英股總市值"""
    try:
        if fubon_df.empty:
            return 0.0, 0.0
        
        value_usd_col = None
        value_ntd_col = None
        
        for col in fubon_df.columns:
            if '市值' in col and 'USD' in col:
                value_usd_col = col
            elif '市值' in col and 'NTD' in col:
                value_ntd_col = col
        
        total_value_usd = fubon_df[value_usd_col].sum() if value_usd_col else 0
        total_value_ntd = fubon_df[value_ntd_col].sum() if value_ntd_col else 0
        
        return total_value_usd, total_value_ntd
        
    except Exception as e:
        st.error(f"計算富邦英股總市值失敗: {e}")
        return 0.0, 0.0

# 優化6: 快取資產配置計算
@st.cache_data(ttl=1800)
def get_asset_allocation_data():
    """計算資產配置數據 - 添加快取"""
    try:
        usd_twd_rate = get_usd_twd_rate()
        allocation_data = {category: {'value_twd': 0.0, 'percentage': 0.0} for category in TARGET_ALLOCATION.keys()}
        
        # 批次載入所有需要的數據
        rita_data = load_person_all_data('rita')
        ed_data = load_person_all_data('ed')
        ed_overseas_data = load_person_all_data('ed_overseas')
        
        # 處理台股數據
        for person_data in [rita_data, ed_data]:
            holdings_df = person_data.get('holdings', pd.DataFrame())
            if not holdings_df.empty and '類別' in holdings_df.columns and '目前總市值' in holdings_df.columns:
                for _, row in holdings_df.iterrows():
                    category = row.get('類別', '').strip()
                    if category in allocation_data:
                        value_twd = parse_number(row.get('目前總市值', 0))
                        allocation_data[category]['value_twd'] += value_twd
        
        # 處理海外投資
        schwab_total_usd = get_schwab_total_value(ed_overseas_data.get('schwab', pd.DataFrame()))
        if schwab_total_usd > 0:
            allocation_data['美股個股']['value_twd'] += schwab_total_usd * usd_twd_rate
        
        # 國泰證券處理
        cathay_df = ed_overseas_data.get('cathay', pd.DataFrame())
        if not cathay_df.empty and len(cathay_df.columns) >= 8:
            for _, row in cathay_df.iterrows():
                if len(row) > 7:
                    category = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ''
                    if category in allocation_data and len(row) > 5:
                        value_usd = parse_number(row.iloc[5])
                        if value_usd > 0:
                            allocation_data[category]['value_twd'] += value_usd * usd_twd_rate
        
        # 富邦英股處理
        fubon_df = ed_overseas_data.get('fubon_uk', pd.DataFrame())
        if not fubon_df.empty and len(fubon_df.columns) >= 13:
            value_usd_col_idx = None
            for i, col in enumerate(fubon_df.columns):
                if '市值' in col and 'USD' in col:
                    value_usd_col_idx = i
                    break
            
            if value_usd_col_idx is not None:
                for _, row in fubon_df.iterrows():
                    if len(row) > max(12, value_usd_col_idx):
                        category = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ''
                        if category in allocation_data:
                            value_usd = parse_number(row.iloc[value_usd_col_idx])
                            if value_usd > 0:
                                allocation_data[category]['value_twd'] += value_usd * usd_twd_rate
        
        # 計算百分比
        total_value = sum([data['value_twd'] for data in allocation_data.values()])
        
        if total_value > 0:
            for category in allocation_data:
                allocation_data[category]['percentage'] = (allocation_data[category]['value_twd'] / total_value) * 100
        
        return allocation_data, total_value, usd_twd_rate
        
    except Exception as e:
        st.error(f"計算資產配置失敗: {e}")
        return {}, 0.0, 31.0

# 優化7: 快取格式化函數
@st.cache_data
def format_currency(amount, currency='TWD', show_prefix=True):
    """格式化貨幣 - 添加快取"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    else:
        if show_prefix:
            return f"NT${amount:,.0f}"
        else:
            return f"{amount:,.0f}"

@st.cache_data
def format_percentage(value):
    """格式化百分比 - 添加快取"""
    return f"{'+' if value > 0 else ''}{value:.2f}%"

def render_user_selection():
    """渲染使用者選擇按鈕"""
    st.markdown('<div class="user-selection-container"></div>', unsafe_allow_html=True)
    
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

def render_trading_interface(person):
    """渲染交易記錄界面 - 新功能"""
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
    st
