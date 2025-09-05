import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re
import time
import yfinance as yf

### 1. 模組化 - 將所有子模組的程式碼合併到主檔案中
# -----------------------------------------------------------
# config_module (原 config.py)
# 自定義CSS樣式
def get_custom_css():
    """Load and return custom CSS styles."""
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .main > div {
            padding-top: 1rem;
        }

        /* 隱藏側邊欄 */
        .css-1d391kg {
            display: none;
        }

        /* 主標題區域 */
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }

        .hero-subtitle {
            font-size: 1.2rem;
            margin: 1rem 0 0 0;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }

        /* 使用者選擇按鈕樣式 */
        .user-selection-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            margin: 2rem 0;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }

        .user-btn {
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            color: #2c3e50;
            border: 2px solid rgba(52, 152, 219, 0.2);
            border-radius: 15px;
            padding: 20px 30px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 150px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }

        .user-btn:before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
            transition: left 0.5s;
        }

        .user-btn:hover:before {
            left: 100%;
        }

        .user-btn:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(52, 152, 219, 0.3);
            border-color: #3498db;
        }

        .user-btn.active {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border-color: #3498db;
            transform: translateY(-5px);
            box-shadow: 0 12px 30px rgba(52, 152, 219, 0.4);
        }

        .user-btn-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }

        .user-btn-label {
            font-size: 1rem;
            font-weight: 600;
        }

        .user-btn-desc {
            font-size: 0.8rem;
            opacity: 0.7;
            margin-top: 4px;
        }

        /* 標籤頁樣式 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(248, 249, 250, 0.8);
            padding: 8px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            padding: 16px 32px;
            color: #6c757d;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            border: none;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(52, 152, 219, 0.1);
            color: #3498db;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3498db, #2980b9) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
        }

        /* 指標卡片 */
        .metric-card {
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            border: 1px solid rgba(0,0,0,0.05);
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            text-align: center;
            margin-bottom: 1.5rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c, #f39c12);
        }

        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 1rem 0;
            color: #2c3e50;
        }

        .metric-label {
            font-size: 1rem;
            color: #7f8c8d;
            font-weight: 500;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-change {
            font-size: 0.9rem;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
        }

        .profit { 
            color: #27ae60; 
            background: rgba(39, 174, 96, 0.1);
        }
        .loss { 
            color: #e74c3c; 
            background: rgba(231, 76, 60, 0.1);
        }

        /* DCA卡片 */
        .dca-card {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(243, 156, 18, 0.3);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        .dca-card::before {
            content: '📊';
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 2rem;
            opacity: 0.3;
        }

        .dca-item {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .dca-item:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateX(5px);
        }

        /* 嘉信+國泰卡片樣式 */
        .schwab-card {
            background: linear-gradient(135deg, #1f4e79, #2e6da4);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(31, 78, 121, 0.3);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        .cathay-card {
            background: linear-gradient(135deg, #8b0000, #dc143c);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(139, 0, 0, 0.3);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        /* 富邦英股卡片樣式 */
        .fubon-card {
            background: linear-gradient(135deg, #2d3436, #636e72);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(45, 52, 54, 0.3);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        /* 資產配置卡片樣式 */
        .allocation-card {
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(108, 92, 231, 0.3);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        /* 圖表區域 */
        .chart-container {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            margin-bottom: 2rem;
            border: 1px solid rgba(0,0,0,0.05);
        }

        /* 表格美化 */
        .dataframe {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        }

        /* 更新按鈕 */
        .stButton > button {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(52, 152, 219, 0.4);
        }

        /* 響應式設計 */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            .hero-section {
                padding: 2rem 1rem;
            }
            .metric-card {
                padding: 1.5rem;
            }
            .user-selection-container {
                flex-direction: column;
                align-items: center;
            }
            .user-btn {
                min-width: 200px;
            }
        }
    </style>
    """

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

# 支援定期定額的用戶
DCA_TARGET_PERSONS = ['jason', 'rita', 'ed']

# 緩存過期時間 (TTL)
CACHE_TTL = {
    'general_data': 600,  # 10 minutes
    'fx_rate': 3600,      # 1 hour
    'long_term_data': 86400 # 24 hours
}

# utils_module (原 utils.py)
def parse_number(value):
    """解析數字，處理各種格式"""
    if isinstance(value, (int, float)):
        return float(value)
    if not value or value == '':
        return 0.0
    
    cleaned = str(value).replace(',', '').replace('%', '').replace('"', '')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def format_currency(amount, currency='TWD', show_prefix=True):
    """格式化貨幣"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    else:
        if show_prefix:
            return f"NT${amount:,.0f}"
        else:
            return f"{amount:,.0f}"

def format_stock_price(price):
    """格式化股價"""
    return f"{price:.2f}"

def format_shares(shares):
    """格式化持股數"""
    return f"{shares:,.0f}"

def format_percentage(value):
    """格式化百分比"""
    return f"{'+' if value > 0 else ''}{value:.2f}%"

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

# data_manager_module (原 data_manager.py)
@st.cache_resource
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

@st.cache_data(ttl=CACHE_TTL['fx_rate'])
def get_usd_twd_rate():
    """取得USDTWD 匯率"""
    try:
        ticker = yf.Ticker("USDTWD=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return 31.0
    except Exception as e:
        st.warning(f"無法獲得即時匯率: {e}，使用預設值 31.0")
        return 31.0

@st.cache_data(ttl=CACHE_TTL['general_data'])
def load_sheet_data(person, data_type):
    """從Google Sheets載入數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        config = SHEET_CONFIGS.get(person)
        if not config:
            st.error(f"找不到使用者 '{person}' 的配置。")
            return pd.DataFrame()
        
        if person == 'ed_overseas':
            broker_config = config.get(data_type)
            if not broker_config:
                st.error(f"找不到券商 '{data_type}' 的配置。")
                return pd.DataFrame()
            sheet_id = broker_config['id']
            range_name = broker_config['range']
        else:
            sheet_id = config['id']
            range_name = config.get(f'{data_type}_range')
            if not range_name:
                return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            st.warning(f"Google Sheet '{range_name}' 中找不到數據。")
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # 數據類型轉換
        for col in df.columns:
            if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率', '金額']):
                df[col] = df[col].apply(parse_number)
        
        return df
        
    except Exception as e:
        st.error(f"載入{person} {data_type}數據失敗: {e}")
        return pd.DataFrame()

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
    """從國泰證券的F欄計算總市值"""
    try:
        if cathay_df.empty or '目前總市值' not in cathay_df.columns:
            return 0.0
        total = cathay_df['目前總市值'].sum()
        return total
    except Exception as e:
        st.error(f"計算國泰證券總市值失敗: {e}")
        return 0.0

def get_fubon_uk_total_value(fubon_df):
    """計算富邦英股總市值"""
    try:
        if fubon_df.empty:
            return 0.0, 0.0
        
        value_usd_col = next((col for col in fubon_df.columns if '市值' in col and 'USD' in col), None)
        value_ntd_col = next((col for col in fubon_df.columns if '市值' in col and 'NTD' in col), None)
        
        total_value_usd = fubon_df[value_usd_col].sum() if value_usd_col else 0
        total_value_ntd = fubon_df[value_ntd_col].sum() if value_ntd_col else 0
        
        return total_value_usd, total_value_ntd
    except Exception as e:
        st.error(f"計算富邦英股總市值失敗: {e}")
        return 0.0, 0.0

@st.cache_data(ttl=CACHE_TTL['general_data'])
def get_asset_allocation_data():
    """計算資產配置數據"""
    try:
        usd_twd_rate = get_usd_twd_rate()
        allocation_data = {category: {'value_twd': 0.0, 'percentage': 0.0} for category in TARGET_ALLOCATION.keys()}
        
        with st.spinner('載入Rita台股...'):
            rita_df = load_sheet_data('rita', 'holdings')
        if not rita_df.empty and '類別' in rita_df.columns and '目前總市值' in rita_df.columns:
            for _, row in rita_df.iterrows():
                category = row.get('類別', '').strip()
                if category in allocation_data:
                    allocation_data[category]['value_twd'] += parse_number(row.get('目前總市值', 0))
        
        with st.spinner('載入Ed台股...'):
            ed_df = load_sheet_data('ed', 'holdings')
        if not ed_df.empty and '類別' in ed_df.columns and '目前總市值' in ed_df.columns:
            for _, row in ed_df.iterrows():
                category = row.get('類別', '').strip()
                if category in allocation_data:
                    allocation_data[category]['value_twd'] += parse_number(row.get('目前總市值', 0))
        
        with st.spinner('載入Ed海外投資...'):
            schwab_df = load_sheet_data('ed_overseas', 'schwab')
            cathay_df = load_sheet_data('ed_overseas', 'cathay')
            fubon_df = load_sheet_data('ed_overseas', 'fubon_uk')

        schwab_total_usd = get_schwab_total_value(schwab_df)
        if schwab_total_usd > 0:
            allocation_data['美股個股']['value_twd'] += schwab_total_usd * usd_twd_rate
        
        if not cathay_df.empty and '類別' in cathay_df.columns and '目前總市值' in cathay_df.columns:
            for _, row in cathay_df.iterrows():
                category = row.get('類別', '').strip()
                if category in allocation_data:
                    value_usd = parse_number(row.get('目前總市值', 0))
                    if value_usd > 0:
                        allocation_data[category]['value_twd'] += value_usd * usd_twd_rate
        
        if not fubon_df.empty:
            value_usd_col = next((col for col in fubon_df.columns if '市值' in col and 'USD' in col), None)
            category_col = next((col for col in fubon_df.columns if '類別' in col), None)

            if value_usd_col and category_col:
                for _, row in fubon_df.iterrows():
                    category = str(row.get(category_col, '')).strip()
                    if category in allocation_data:
                        value_usd = parse_number(row.get(value_usd_col, 0))
                        if value_usd > 0:
                            allocation_data[category]['value_twd'] += value_usd * usd_twd_rate

        total_value = sum([data['value_twd'] for data in allocation_data.values()])
        
        if total_value > 0:
            for category in allocation_data:
                allocation_data[category]['percentage'] = (allocation_data[category]['value_twd'] / total_value) * 100
        
        return allocation_data, total_value, usd_twd_rate
        
    except Exception as e:
        st.error(f"計算資產配置失敗: {e}")
        return {}, 0.0, 31.0

# ui_module (原 ui.py)
def render_header():
    """Renders the main hero section of the app."""
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)

def render_user_selection():
    """Renders user selection buttons."""
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

def render_summary_cards(person, holdings_df, dca_df):
    """Renders summary cards for a specific person's portfolio."""
    if holdings_df.empty:
        return
    
    try:
        total_cost = holdings_df['總投入成本'].sum()
        total_value = holdings_df['目前總市值'].sum()
        total_pl = holdings_df['未實現損益'].sum()
        total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">總投入成本</div><div class="metric-value">{format_currency(total_cost)}</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">目前市值</div><div class="metric-value">{format_currency(total_value)}</div></div>', unsafe_allow_html=True)
        
        with col3:
            profit_class = 'profit' if total_pl >= 0 else 'loss'
            st.markdown(f'<div class="metric-card"><div class="metric-label">未實現損益</div><div class="metric-value {profit_class}">{format_currency(total_pl)}</div><div class="metric-change {profit_class}">{format_percentage(total_return)}</div></div>', unsafe_allow_html=True)
        
        with col4:
            render_dca_card(dca_df)
    except Exception as e:
        st.error(f"台股投資摘要卡片渲染錯誤: {e}")

def render_dca_card(dca_df):
    """Renders the DCA (Dollar-Cost Averaging) card."""
    with st.container():
        st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div></div>', unsafe_allow_html=True)
        if dca_df is not None and not dca_df.empty and all(col in dca_df.columns for col in ['股票代號', '股票名稱', '每月投入金額', '扣款日']):
            for _, row in dca_df.iterrows():
                if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                    st.markdown(f'<div class="dca-item"><strong>{row["股票代號"]} {row["股票名稱"]}</strong><br><small>每月{format_currency(row["每月投入金額"])} | {int(row["扣款日"])}號扣款</small></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div><div style="opacity: 0.8;">暫無設定資料或格式錯誤</div></div>', unsafe_allow_html=True)

def render_ed_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd):
    """Renders summary cards for Ed's overseas investments."""
    total_combined_usd = schwab_total_usd + cathay_total_usd + fubon_total_usd
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="schwab-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇺🇸 嘉信證券</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(schwab_total_usd, "USD")}</div><div style="opacity: 0.8;">美股個股總市值</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="cathay-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇹🇼 國泰證券</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(cathay_total_usd, "USD")}</div><div style="opacity: 0.8;">美股ETF總市值</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="fubon-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇬🇧 富邦英股</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(fubon_total_usd, "USD")}</div><div style="opacity: 0.8;">英股總市值</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border: none; background: #e8f5e9;"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #388e3c; opacity: 0.9;">總資產 (USD)</div><div style="font-size: 2.5rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem;">{format_currency(total_combined_usd, "USD")}</div><div style="opacity: 0.8;">三平台合計</div></div>', unsafe_allow_html=True)

def render_holdings_tab(holdings_df, show_chart=False):
    """Renders the holdings table and chart."""
    if holdings_df.empty:
        st.info("查無持股數據。")
        return
    
    if show_chart:
        render_portfolio_chart(holdings_df)
    else:
        st.dataframe(
            holdings_df.style.format({
                '目前股價': "{:.2f}",
                '總持有股數': "{:,.0f}",
                '總投入成本': "NT${:,.0f}",
                '目前總市值': "NT${:,.0f}",
                '未實現損益': "NT${:,.0f}",
                '報酬率': "{:,.2f}%"
            }),
            use_container_width=True
        )

def render_portfolio_chart(holdings_df):
    """Generates and renders a portfolio pie chart."""
    if holdings_df.empty or '股票名稱' not in holdings_df.columns or '目前總市值' not in holdings_df.columns:
        st.warning("數據格式不正確，無法繪製資產配置圖。")
        return
        
    portfolio_df = holdings_df[['股票名稱', '目前總市值']].copy()
    portfolio_df = portfolio_df[portfolio_df['目前總市值'] > 0]
    fig = px.pie(
        portfolio_df, values='目前總市值', names='股票名稱', 
        title='資產配置 (按市值)', hole=0.4,
        color_discrete_sequence=px.colors.sequential.Agsunset
    )
    fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
    st.plotly_chart(fig, use_container_width=True)

def render_trend_chart(trend_df):
    """Generates and renders the asset trend chart."""
    if trend_df is None or trend_df.empty:
        st.info("查無資產趨勢數據。")
        return
    try:
        trend_df = trend_df.copy()
        if '日期' not in trend_df.columns or '總市值' not in trend_df.columns:
            st.warning("趨勢數據格式不正確，無法繪製圖表。")
            return
            
        trend_df['日期'] = pd.to_datetime(trend_df['日期'])
        trend_df['總市值'] = trend_df['總市值'].apply(parse_number)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['日期'], y=trend_df['總市值'], mode='lines+markers', name='總市值',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8, color='#3498db', line=dict(width=1, color='DarkSlateGrey'))
        ))
        fig.update_layout(
            title='資產趨勢', xaxis_title='日期', yaxis_title='總市值 (NT$)',
            hovermode='x unified', template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"資產趨勢圖繪製失敗: {e}")

def render_overseas_holdings_tabs(schwab_df, cathay_df, fubon_df):
    """Renders tabs for overseas holdings."""
    tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 嘉信證券", "🇹🇼 國泰證券", "🇬🇧 富邦英股", "📊 綜合分析"])
    
    with tab1:
        st.subheader("嘉信證券 - 美股個股")
        render_overseas_table_and_chart(schwab_df, "嘉信證券")

    with tab2:
        st.subheader("國泰證券 - 美股ETF")
        render_overseas_table_and_chart(cathay_df, "國泰證券")
    
    with tab3:
        st.subheader("富邦證券 - 英股投資")
        render_overseas_table_and_chart(fubon_df, "富邦英股")
    
    with tab4:
        st.subheader("綜合投資分析")
        render_combined_bar_chart(schwab_df, cathay_df, fubon_df)

def render_overseas_table_and_chart(df, broker_name):
    """Renders table and chart for a specific overseas broker."""
    if df.empty:
        st.info(f"查無{broker_name}持股數據。")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        render_overseas_portfolio_chart(df, broker_name)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if broker_name == "富邦英股":
            display_df = df.rename(columns={
                '目前美價': '美價(USD)', '總持有股數': '股數',
                '總投入成本(USD)': '成本(USD)', '目前總市值(USD)': '市值(USD)',
                '未實現損益(USD)': '損益(USD)', '未實現報酬率': '報酬率%',
                '總未實現損益%': '總報酬率%'
            })
            display_columns = ['股票代號', '股票名稱', '美價(USD)', '股數', '成本(USD)', '市值(USD)', '損益(USD)', '報酬率%']
            display_columns = [col for col in display_columns if col in display_df.columns]
            st.dataframe(
                display_df[display_columns].style.format({
                    '美價(USD)': "{:.2f}", '股數': "{:,.0f}",
                    '成本(USD)': "${:,.0f}", '市值(USD)': "${:,.0f}",
                    '損益(USD)': "${:,.0f}", '報酬率%': "{:,.2f}%"
                }),
                use_container_width=True
            )
        else:
            st.dataframe(df, use_container_width=True)

def render_overseas_portfolio_chart(df, broker_name):
    """Renders a pie chart for overseas holdings."""
    if df.empty: return
    try:
        value_col = next((col for col in df.columns if '市值' in col and ('USD' in col or 'NTD' not in col)), None)
        name_col = next((col for col in df.columns if '名稱' in col), None)
        if not value_col or not name_col:
            st.warning(f"找不到{broker_name}的市值或名稱欄位，無法繪製圖表。")
            return
            
        portfolio_df = df[[name_col, value_col]].copy()
        portfolio_df = portfolio_df[portfolio_df[value_col] > 0]
        
        fig = px.pie(
            portfolio_df, values=value_col, names=name_col, 
            title=f'{broker_name} 資產配置 (按市值)', hole=0.4,
            color_discrete_sequence=px.colors.sequential.Plasma_r
        )
        fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"{broker_name}圖表繪製失敗: {e}")

def render_combined_bar_chart(schwab_df, cathay_df, fubon_df):
    """Renders a combined bar chart of all overseas platforms."""
    schwab_total_usd = get_schwab_total_value(schwab_df)
    cathay_total_usd = get_cathay_total_value(cathay_df)
    fubon_total_usd, _ = get_fubon_uk_total_value(fubon_df)
    
    platforms = ['嘉信證券', '國泰證券', '富邦英股']
    values = [schwab_total_usd, cathay_total_usd, fubon_total_usd]
    
    fig = px.bar(
        x=platforms, y=values, title='各平台投資總值比較 (USD)',
        color=platforms, color_discrete_sequence=['#1f4e79', '#8b0000', '#2d3436']
    )
    fig.update_layout(showlegend=False, yaxis_title='總市值 (USD)')
    st.plotly_chart(fig, use_container_width=True)

def render_asset_allocation_section(allocation_data, total_value, usd_twd_rate):
    """Renders the asset allocation summary and charts."""
    st.subheader("🎯 目標 vs 實際配置比較")
    
    if total_value <= 0:
        st.warning("無法取得資產配置數據，請檢查數據來源。")
        return
        
    categories = list(TARGET_ALLOCATION.keys())
    target_percentages = [TARGET_ALLOCATION[cat] for cat in categories]
    actual_percentages = [allocation_data[cat]['percentage'] for cat in categories]
    actual_values = [allocation_data[cat]['value_twd'] for cat in categories]
    differences = [actual - target for actual, target in zip(actual_percentages, target_percentages)]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">總資產</div><div class="metric-value">{format_currency(total_value)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">USD/TWD 匯率</div><div class="metric-value">{usd_twd_rate:.2f}</div></div>', unsafe_allow_html=True)
    
    comparison_df = pd.DataFrame({
        '資產類別': categories,
        '目標配置(%)': target_percentages,
        '實際配置(%)': [f"{x:.1f}" for x in actual_percentages],
        '實際金額(台幣)': [format_currency(x, show_prefix=False) for x in actual_values],
        '差距(%)': [f"{'+' if x > 0 else ''}{x:.1f}" for x in differences]
    })
    
    st.markdown("### 📊 配置詳細比較")
    st.dataframe(
        comparison_df.style.format({'目標配置(%)': "{:.0f}%"}).applymap(
            lambda x: 'color: green' if isinstance(x, str) and x.startswith('+') else ('color: red' if isinstance(x, str) and x.startswith('-') else ''),
            subset=['差距(%)']
        ),
        use_container_width=True
    )
    
    st.markdown("---")
    render_allocation_charts(categories, target_percentages, actual_percentages, differences)
    
    st.markdown("### 💡 配置建議")
    suggestions = []
    for i, (cat, diff) in enumerate(zip(categories, differences)):
        if abs(diff) > 2:
            if diff > 0:
                suggestions.append(f"• **{cat}** 目前超配 {diff:.1f}%，建議減少投入")
            else:
                suggestions.append(f"• **{cat}** 目前低配 {abs(diff):.1f}%，建議增加投入")
    
    if suggestions:
        for suggestion in suggestions:
            st.markdown(suggestion)
    else:
        st.success("🎉 目前配置與目標相當接近，維持現狀即可！")

def render_allocation_charts(categories, target_percentages, actual_percentages, differences):
    """Renders all allocation charts (bar and pie)."""
    col1, col2 = st.columns(2)
    with col1:
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(name='目標配置', x=categories, y=target_percentages, marker_color='rgba(52, 152, 219, 0.7)'))
        fig_comparison.add_trace(go.Bar(name='實際配置', x=categories, y=actual_percentages, marker_color='rgba(231, 76, 60, 0.7)'))
        fig_comparison.update_layout(title='目標 vs 實際配置比較', xaxis_title='資產類別', yaxis_title='配置比例(%)', barmode='group', template="plotly_white")
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    with col2:
        colors = ['green' if x >= 0 else 'red' for x in differences]
        fig_diff = go.Figure(data=[go.Bar(x=categories, y=differences, marker_color=colors, text=[f"{x:+.1f}%" for x in differences], textposition='auto')])
        fig_diff.update_layout(title='配置差距 (實際 - 目標)', xaxis_title='資產類別', yaxis_title='差距(%)', template="plotly_white", yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'))
        st.plotly_chart(fig_diff, use_container_width=True)
    
    col3, col4 = st.columns(2)
    with col3:
        fig_target_pie = px.pie(values=target_percentages, names=categories, title='目標資產配置', color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_target_pie, use_container_width=True)
    with col4:
        fig_actual_pie = px.pie(values=actual_percentages, names=categories, title='實際資產配置', color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_actual_pie, use_container_width=True)

# -----------------------------------------------------------
# 主應用程式邏輯 (原 app.py main)
# -----------------------------------------------------------
def main():
    """Main application logic"""
    
    # Render the main page header
    render_header()
    
    # Select the current user/view
    selected_person = render_user_selection()
    
    # Add a refresh button to clear cache and reload data
    if st.button('更新數據', key='refresh_button'):
        st.cache_data.clear()
        st.rerun()

    if selected_person == 'asset_allocation':
        st.header("📊 整體資產配置分析")
        
        with st.spinner('正在計算資產配置...'):
            allocation_data, total_value, usd_twd_rate = get_asset_allocation_data()
        
        render_asset_allocation_section(allocation_data, total_value, usd_twd_rate)
        
    elif selected_person == 'ed_overseas':
        st.header("Ed 海外投資總覽")
        
        with st.spinner('正在載入海外投資數據...'):
            schwab_df = load_sheet_data('ed_overseas', 'schwab')
            cathay_df = load_sheet_data('ed_overseas', 'cathay')
            fubon_df = load_sheet_data('ed_overseas', 'fubon_uk')
        
        schwab_total_usd = get_schwab_total_value(schwab_df)
        cathay_total_usd = get_cathay_total_value(cathay_df)
        fubon_total_usd, _ = get_fubon_uk_total_value(fubon_df)
        
        render_ed_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd)
        
        render_overseas_holdings_tabs(schwab_df, cathay_df, fubon_df)
        
        # New Feature: Add record to Schwab
        st.markdown("---")
        with st.form("schwab_append_form", clear_on_submit=True):
            st.write("##### ✏️ 新增一筆嘉信總市值紀錄")
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                record_date = st.date_input("紀錄日期", value=datetime.now())
            with c2:
                market_value = st.number_input("總市值 (USD)", min_value=0.0, format="%.2f")
            with c3:
                st.write("")
                st.write("")
                submitted = st.form_submit_button("新增至 Google Sheet")
        
        if submitted:
            sheet_id = SHEET_CONFIGS['ed_overseas']['schwab']['id']
            worksheet_name = 'schwab'
            date_str = record_date.strftime('%Y/%m/%d')
            values_to_append = [[date_str, market_value]]
            
            success = append_to_sheet(sheet_id, worksheet_name, values_to_append)
            
            if success:
                st.success("紀錄已成功新增！正在重新整理數據...")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("新增紀錄失敗，請檢查後台日誌或 API 權限。")

    else:
        st.header(f"{selected_person.capitalize()} 台股投資總覽")
        
        with st.spinner(f"正在載入 {selected_person.capitalize()} 的數據..."):
            holdings_df = load_sheet_data(selected_person, 'holdings')
            
        # Only load DCA and Trend if needed
        dca_df = None
        trend_df = None
        if selected_person in DCA_TARGET_PERSONS:
            dca_df = load_sheet_data(selected_person, 'dca')
            trend_df = load_sheet_data(selected_person, 'trend')

        if not holdings_df.empty:
            render_summary_cards(selected_person, holdings_df, dca_df)
            
            tab1, tab2, tab3 = st.tabs(["📈 持股明細", "🥧 資產配置", "📊 資產趨勢"])
            
            with tab1:
                st.subheader("持股明細")
                render_holdings_tab(holdings_df)
            with tab2:
                st.subheader("資產配置")
                render_holdings_tab(holdings_df, show_chart=True)
            with tab3:
                st.subheader("資產趨勢")
                render_trend_chart(trend_df)
        else:
            st.warning(f"無法載入 {selected_person.capitalize()} 的投資數據，或數據為空。")

if __name__ == "__main__":
    st.set_page_config(
        page_title="投資總覽",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    main()
