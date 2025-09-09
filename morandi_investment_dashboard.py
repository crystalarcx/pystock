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

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 莫蘭迪配色 CSS 樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        /* 莫蘭迪核心色調 */
        --morandi-sage: #9CAF88;
        --morandi-dusty-rose: #C4A484;
        --morandi-clay: #B5A28F;
        --morandi-stone: #9B8E7E;
        --morandi-mist: #A8A5A0;
        --morandi-cream: #F5F2E8;
        --morandi-soft-white: #FDFCF7;
        --morandi-warm-grey: #D4CFC7;
        --morandi-deep-sage: #7A8471;
        --morandi-terracotta: #B89080;
        --morandi-lavender: #ACA4B2;
        --morandi-olive: #8B8C6B;
        
        /* 功能性顏色 */
        --success-morandi: #8FA68E;
        --danger-morandi: #B8938A;
        --warning-morandi: #C4A962;
        --info-morandi: #93A3B1;
        
        /* 文字顏色 */
        --text-primary: #4A453F;
        --text-secondary: #6B645C;
        --text-muted: #8B8680;
    }
    
    * { 
        font-family: 'Inter', sans-serif; 
        font-weight: 400;
    }
    
    .main > div { padding-top: 1rem; }
    .css-1d391kg { display: none; }
    
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, var(--morandi-soft-white) 0%, var(--morandi-cream) 100%);
    }
    
    /* 主標題區域 - 莫蘭迪風格 */
    .hero-section {
        background: linear-gradient(135deg, var(--morandi-sage) 0%, var(--morandi-deep-sage) 50%, var(--morandi-stone) 100%);
        color: var(--morandi-soft-white);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2.5rem;
        text-align: center;
        box-shadow: 0 12px 40px rgba(156, 175, 136, 0.15);
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(245, 242, 232, 0.1) 0%, transparent 70%);
        animation: subtle-pulse 8s ease-in-out infinite;
    }
    
    @keyframes subtle-pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    
    .hero-title {
        font-size: 2.8rem;
        font-weight: 300;
        margin: 0;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        margin: 1.5rem 0 0 0;
        opacity: 0.85;
        font-weight: 300;
        position: relative;
        z-index: 1;
    }
    
    /* 用戶選擇按鈕 - 莫蘭迪風格 */
    .user-selection-container {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        justify-content: center;
        margin: 2rem 0;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(212, 207, 199, 0.3), rgba(168, 165, 160, 0.2));
        border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    
    .user-btn {
        background: linear-gradient(135deg, var(--morandi-soft-white), var(--morandi-warm-grey));
        color: var(--text-primary);
        border: 2px solid rgba(156, 175, 136, 0.3);
        border-radius: 16px;
        padding: 20px 28px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-decoration: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 140px;
        box-shadow: 0 6px 20px rgba(156, 175, 136, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .user-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(156, 175, 136, 0.1), transparent);
        transition: left 0.5s;
    }
    
    .user-btn:hover::before {
        left: 100%;
    }
    
    .user-btn:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(156, 175, 136, 0.2);
        border-color: var(--morandi-sage);
    }
    
    .user-btn.active {
        background: linear-gradient(135deg, var(--morandi-sage), var(--morandi-deep-sage));
        color: var(--morandi-soft-white);
        border-color: var(--morandi-deep-sage);
        box-shadow: 0 8px 25px rgba(122, 132, 113, 0.3);
    }
    
    /* 標籤頁 - 莫蘭迪風格 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, var(--morandi-cream), var(--morandi-warm-grey));
        padding: 8px;
        border-radius: 14px;
        box-shadow: inset 0 2px 8px rgba(156, 175, 136, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        padding: 14px 28px;
        color: var(--text-secondary);
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--morandi-sage), var(--morandi-deep-sage)) !important;
        color: var(--morandi-soft-white) !important;
        box-shadow: 0 4px 12px rgba(156, 175, 136, 0.3);
    }
    
    /* 指標卡片 - 莫蘭迪風格 */
    .metric-card {
        background: linear-gradient(135deg, var(--morandi-soft-white), var(--morandi-cream));
        border: 1px solid rgba(156, 175, 136, 0.15);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 25px rgba(156, 175, 136, 0.08);
        text-align: center;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
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
        background: linear-gradient(90deg, var(--morandi-sage), var(--morandi-dusty-rose), var(--morandi-clay), var(--morandi-lavender));
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(156, 175, 136, 0.15);
    }
    
    .metric-value {
        font-size: 2.4rem;
        font-weight: 600;
        margin: 1rem 0;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }
    
    .metric-label {
        font-size: 0.95rem;
        color: var(--text-muted);
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
        letter-spacing: 0.3px;
    }
    
    .profit { 
        color: var(--success-morandi); 
        background: linear-gradient(135deg, rgba(143, 166, 142, 0.15), rgba(122, 132, 113, 0.1)); 
    }
    
    .loss { 
        color: var(--danger-morandi); 
        background: linear-gradient(135deg, rgba(184, 147, 138, 0.15), rgba(184, 147, 138, 0.1)); 
    }
    
    /* 專用卡片 - 莫蘭迪配色方案 */
    .dca-card {
        background: linear-gradient(135deg, var(--morandi-dusty-rose), var(--morandi-clay));
        color: var(--morandi-soft-white);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(196, 164, 132, 0.2);
    }
    
    .schwab-card {
        background: linear-gradient(135deg, var(--morandi-stone), var(--morandi-mist));
        color: var(--morandi-soft-white);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(155, 142, 126, 0.2);
    }
    
    .cathay-card {
        background: linear-gradient(135deg, var(--morandi-terracotta), var(--danger-morandi));
        color: var(--morandi-soft-white);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(184, 144, 128, 0.2);
    }
    
    .fubon-card {
        background: linear-gradient(135deg, var(--morandi-lavender), var(--info-morandi));
        color: var(--morandi-soft-white);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(172, 164, 178, 0.2);
    }
    
    .allocation-card {
        background: linear-gradient(135deg, var(--morandi-olive), var(--morandi-sage));
        color: var(--morandi-soft-white);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(139, 140, 107, 0.2);
    }
    
    .dca-item {
        background: rgba(245, 242, 232, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(245, 242, 232, 0.1);
    }
    
    /* 圖表容器 - 莫蘭迪風格 */
    .chart-container {
        background: linear-gradient(135deg, var(--morandi-soft-white), var(--morandi-cream));
        border: 1px solid rgba(156, 175, 136, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 25px rgba(156, 175, 136, 0.08);
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* 按鈕樣式 - 莫蘭迪風格 */
    .stButton > button {
        background: linear-gradient(135deg, var(--morandi-sage), var(--morandi-deep-sage));
        color: var(--morandi-soft-white);
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(156, 175, 136, 0.2);
        letter-spacing: 0.3px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(156, 175, 136, 0.3);
    }
    
    /* 表格樣式美化 */
    .dataframe {
        background: var(--morandi-soft-white) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 15px rgba(156, 175, 136, 0.1) !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, var(--morandi-sage), var(--morandi-deep-sage)) !important;
        color: var(--morandi-soft-white) !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        border: none !important;
    }
    
    .dataframe td {
        padding: 10px 16px !important;
        border-bottom: 1px solid rgba(156, 175, 136, 0.1) !important;
        color: var(--text-primary) !important;
    }
    
    .dataframe tr:hover {
        background: rgba(156, 175, 136, 0.05) !important;
    }
    
    /* 表單樣式 */
    .stSelectbox > div > div {
        background: var(--morandi-soft-white);
        border: 1px solid rgba(156, 175, 136, 0.3);
        border-radius: 8px;
    }
    
    .stNumberInput > div > div > input {
        background: var(--morandi-soft-white);
        border: 1px solid rgba(156, 175, 136, 0.3);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    .stDateInput > div > div > input {
        background: var(--morandi-soft-white);
        border: 1px solid rgba(156, 175, 136, 0.3);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* 分隔線 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--morandi-sage), transparent);
        margin: 2rem 0;
    }
    
    /* 警告和信息框 */
    .stAlert > div {
        border-radius: 12px;
        border: 1px solid rgba(156, 175, 136, 0.2);
        background: linear-gradient(135deg, var(--morandi-soft-white), var(--morandi-cream));
    }
    
    .stSuccess > div {
        background: linear-gradient(135deg, rgba(143, 166, 142, 0.1), rgba(122, 132, 113, 0.05));
        border-color: var(--success-morandi);
    }
    
    .stError > div {
        background: linear-gradient(135deg, rgba(184, 147, 138, 0.1), rgba(184, 147, 138, 0.05));
        border-color: var(--danger-morandi);
    }
    
    .stWarning > div {
        background: linear-gradient(135deg, rgba(196, 169, 98, 0.1), rgba(196, 169, 98, 0.05));
        border-color: var(--warning-morandi);
    }
    
    .stInfo > div {
        background: linear-gradient(135deg, rgba(147, 163, 177, 0.1), rgba(147, 163, 177, 0.05));
        border-color: var(--info-morandi);
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.2rem; }
        .hero-section { padding: 2rem 1.5rem; }
        .metric-card { padding: 1.5rem; }
        .user-btn { min-width: 120px; padding: 16px 20px; }
    }
    
    /* 微妙的動畫效果 */
    @keyframes gentle-glow {
        0%, 100% { box-shadow: 0 8px 25px rgba(156, 175, 136, 0.08); }
        50% { box-shadow: 0 12px 35px rgba(156, 175, 136, 0.12); }
    }
    
    .metric-card:hover {
        animation: gentle-glow 2s ease-in-out infinite;
    }
    
    /* Plotly 圖表色彩調整 */
    .js-plotly-plot .plotly {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets 配置
SHEET_CONFIGS = {
    'jason': {
        'id': '17qQIU4KMtbTpo_ozguuzKFHf1HHOhuEBanXxCyE8k4M',
        'holdings_range': '總覽與獲益!A:I',
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'rita': {
        'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
        'holdings_range': '總覽與獲益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'ed': {
        'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
        'holdings_range': '總覽與獲益!A:I', 
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
            'range': '總覽與獲益!A:Z'
        },
        'fubon_uk': {
            'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
            'range': '總覽與獲益!A:M'
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
            numeric_columns = [col for col in df.columns if any(keyword in col for keyword in ['價', '成本', '市值', '獲益', '股數', '率'])]
        elif data_type == 'holdings':
            numeric_columns = ['總投入成本', '總持有股數', '目前股價', '目前總市值', '未實現獲益', '報酬率']
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
    """從總覽與獲益工作表的F欄計算總市值"""
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
        {'key': 'ed_overseas', 'icon': '🌍', 'label': 'Ed', 'desc': '海外總覽'},
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
    """渲染摘要卡片 - 簡化錯誤處理"""
    if person in ['ed_overseas', 'asset_allocation']:
        return
    
    try:
        required_columns = ['總投入成本', '目前總市值', '未實現獲益']
        if not all(col in holdings_df.columns for col in required_columns) or holdings_df.empty:
            st.warning("持股數據不完整或為空")
            return
        
        total_cost = holdings_df['總投入成本'].sum()
        total_value = holdings_df['目前總市值'].sum()
        total_pl = holdings_df['未實現獲益'].sum()
        total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">總投入成本</div><div class="metric-value">{format_currency(total_cost)}</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">目前市值</div><div class="metric-value">{format_currency(total_value)}</div></div>', unsafe_allow_html=True)
        
        with col3:
            profit_class = 'profit' if total_pl >= 0 else 'loss'
            st.markdown(f'<div class="metric-card"><div class="metric-label">未實現獲益</div><div class="metric-value {profit_class}">{format_currency(total_pl)}</div><div class="metric-change {profit_class}">{format_percentage(total_return)}</div></div>', unsafe_allow_html=True)
        
        with col4:
            if dca_df is not None and not dca_df.empty and all(col in dca_df.columns for col in ['股票代號', '股票名稱', '每月投入金額', '扣款日']):
                with st.container():
                    st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">定期定額設定</div></div>', unsafe_allow_html=True)
                    for _, row in dca_df.iterrows():
                        if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                            monthly_amount = parse_number(row.get('每月投入金額', 0))
                            deduction_day = int(parse_number(row.get('扣款日', 0)))
                            st.markdown(f'<div class="dca-item"><strong>{row["股票代號"]} {row["股票名稱"]}</strong><br><small>每月{format_currency(monthly_amount)} | {deduction_day}號扣款</small></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">定期定額設定</div><div style="opacity: 0.8;">暫無設定資料</div></div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"台股投資摘要卡片渲染錯誤: {str(e)}")

def render_ed_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd, fubon_total_ntd):
    """渲染ED海外投資綜合摘要卡片"""
    total_combined_usd = schwab_total_usd + cathay_total_usd + fubon_total_usd
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="schwab-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇺🇸 嘉信證券</div><div style="font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(schwab_total_usd, "USD")}</div><div style="opacity: 0.8;">美股個股總市值</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="cathay-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇹🇼 國泰證券</div><div style="font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(cathay_total_usd, "USD")}</div><div style="opacity: 0.8;">美股ETF總市值</div></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="fubon-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇬🇧 富邦英股</div><div style="font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(fubon_total_usd, "USD")}</div><div style="opacity: 0.8;">英股總市值</div></div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="metric-card" style="border: none; background: linear-gradient(135deg, var(--morandi-sage), var(--morandi-deep-sage));"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: var(--morandi-soft-white); opacity: 0.9;">總資產 (USD)</div><div style="font-size: 2.2rem; font-weight: 700; color: var(--morandi-soft-white); margin-bottom: 0.5rem;">{format_currency(total_combined_usd, "USD")}</div><div style="opacity: 0.8; color: var(--morandi-soft-white);">三平台合計</div></div>', unsafe_allow_html=True)

def render_asset_allocation_summary(allocation_data, total_value, usd_twd_rate):
    """渲染資產配置摘要"""
    st.subheader("🎯 目標 vs 實際配置比較")
    
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
        comparison_df.style.format({
            '目標配置(%)': "{:.0f}%"
        }).applymap(
            lambda x: 'color: green' if isinstance(x, str) and x.startswith('+') 
            else ('color: red' if isinstance(x, str) and x.startswith('-') else ''),
            subset=['差距(%)']
        ),
        use_container_width=True
    )
    
    return categories, target_percentages, actual_percentages, differences

# 優化8: 延緩載入圖表組件
def render_allocation_charts(categories, target_percentages, actual_percentages, differences):
    """渲染資產配置圖表 - 優化版"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 使用 st.empty() 實現條件渲染
        chart_container1 = st.empty()
        with chart_container1.container():
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name='目標配置',
                x=categories,
                y=target_percentages,
                marker_color='#9CAF88'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name='實際配置',
                x=categories,
                y=actual_percentages,
                marker_color='#B8938A'
            ))
            
            fig_comparison.update_layout(
                title='目標 vs 實際配置比較',
                xaxis_title='資產類別',
                yaxis_title='配置比例(%)',
                barmode='group',
                template="plotly_white",
                height=400,
                paper_bgcolor='rgba(253,252,247,0.9)',
                plot_bgcolor='rgba(253,252,247,0.9)'
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    with col2:
        chart_container2 = st.empty()
        with chart_container2.container():
            colors = ['#8FA68E' if x >= 0 else '#B8938A' for x in differences]
            
            fig_diff = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=differences,
                    marker_color=colors,
                    text=[f"{x:+.1f}%" for x in differences],
                    textposition='auto'
                )
            ])
            
            fig_diff.update_layout(
                title='配置差距 (實際 - 目標)',
                xaxis_title='資產類別',
                yaxis_title='差距(%)',
                template="plotly_white",
                height=400,
                yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='#A8A5A0'),
                paper_bgcolor='rgba(253,252,247,0.9)',
                plot_bgcolor='rgba(253,252,247,0.9)'
            )
            
            st.plotly_chart(fig_diff, use_container_width=True)
    
    # 餅狀圖比較 - 簡化版本
    col3, col4 = st.columns(2)
    
    # 莫蘭迪配色方案
    morandi_colors = ['#9CAF88', '#C4A484', '#B5A28F', '#9B8E7E', '#A8A5A0']
    
    with col3:
        fig_target_pie = px.pie(
            values=target_percentages,
            names=categories,
            title='目標資產配置',
            color_discrete_sequence=morandi_colors
        )
        fig_target_pie.update_layout(height=350, paper_bgcolor='rgba(253,252,247,0.9)')
        st.plotly_chart(fig_target_pie, use_container_width=True)
    
    with col4:
        fig_actual_pie = px.pie(
            values=actual_percentages,
            names=categories,
            title='實際資產配置',
            color_discrete_sequence=[c.replace('88', '7A') for c in morandi_colors]  # 稍微暗一點
        )
        fig_actual_pie.update_layout(height=350, paper_bgcolor='rgba(253,252,247,0.9)')
        st.plotly_chart(fig_actual_pie, use_container_width=True)

def render_holdings_table(holdings_df, person):
    """渲染持股表格 - 添加數字格式化"""
    if holdings_df.empty:
        st.info("查無持股數據。")
        return
    
    if person != 'ed_overseas':
        # 格式化數字欄位，添加千位分隔符
        format_dict = {}
        for col in holdings_df.columns:
            if col in ['目前股價']:
                format_dict[col] = "{:.2f}"
            elif col in ['總持有股數']:
                format_dict[col] = "{:,.0f}"
            elif col in ['總投入成本', '目前總市值', '未實現獲益']:
                format_dict[col] = "NT${:,.0f}"
            elif col in ['報酬率']:
                format_dict[col] = "{:,.2f}%"
        
        if format_dict:
            styled_df = holdings_df.style.format(format_dict)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(holdings_df, use_container_width=True)

def render_overseas_holdings_table(df, broker_name):
    """渲染海外持股表格 - 優化版本"""
    if df.empty:
        st.info(f"查無{broker_name}持股數據。")
        return
    
    if broker_name == "富邦英股":
        # 只顯示必要欄位，減少處理時間
        essential_columns = [col for col in df.columns if any(keyword in col for keyword in ['股票代號', '股票名稱', '市值', '獲益', '報酬率'])]
        display_df = df[essential_columns] if essential_columns else df
        st.dataframe(display_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
    
def render_portfolio_chart(holdings_df, person):
    """渲染投資組合圖表 - 優化版本"""
    if holdings_df.empty or person == 'ed_overseas': 
        return
        
    try:
        portfolio_df = holdings_df[['股票名稱', '目前總市值']].copy()
        portfolio_df = portfolio_df[portfolio_df['目前總市值'] > 0]
        
        if portfolio_df.empty:
            return
            
        # 使用莫蘭迪配色
        morandi_colors = ['#9CAF88', '#C4A484', '#B5A28F', '#9B8E7E', '#A8A5A0', 
                         '#B89080', '#ACA4B2', '#8B8C6B', '#93A3B1', '#C4A962']
        
        fig = px.pie(
            portfolio_df, 
            values='目前總市值', 
            names='股票名稱', 
            title='資產配置 (按市值)', 
            hole=0.4,
            color_discrete_sequence=morandi_colors
        )
        fig.update_traces(textinfo='percent+label', pull=[0.05]*len(portfolio_df))
        fig.update_layout(height=400, paper_bgcolor='rgba(253,252,247,0.9)')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"圖表渲染失敗: {str(e)}")

def render_overseas_portfolio_chart(df, broker_name):
    """渲染海外投資組合圖表 - 優化版本"""
    if df.empty: 
        return
    try:
        value_col, name_col = None, None
        for col in df.columns:
            if '市值' in col and ('USD' in col or 'NTD' not in col): 
                value_col = col
                break
        for col in df.columns:
            if '名稱' in col: 
                name_col = col
                break
                
        if not value_col or not name_col:
            return
            
        portfolio_df = df[[name_col, value_col]].copy()
        portfolio_df = portfolio_df[portfolio_df[value_col] > 0]
        
        if portfolio_df.empty:
            return
            
        # 根據不同券商使用不同的莫蘭迪色調
        if '嘉信' in broker_name:
            colors = ['#9B8E7E', '#A8A5A0', '#B5A28F', '#C4A484', '#9CAF88']
        elif '國泰' in broker_name:
            colors = ['#B89080', '#C4A484', '#B5A28F', '#9B8E7E', '#A8A5A0']
        else:  # 富邦
            colors = ['#ACA4B2', '#93A3B1', '#8B8C6B', '#9CAF88', '#B5A28F']
            
        fig = px.pie(
            portfolio_df, 
            values=value_col, 
            names=name_col, 
            title=f'{broker_name} 資產配置 (按市值)', 
            hole=0.4,
            color_discrete_sequence=colors
        )
        fig.update_traces(textinfo='percent+label', pull=[0.05]*len(portfolio_df))
        fig.update_layout(height=400, paper_bgcolor='rgba(253,252,247,0.9)')
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass  # 靜默處理錯誤，避免影響主要流程

def render_trend_chart(trend_df):
    """渲染趨勢圖表 - 優化版本"""
    if trend_df.empty:
        st.info("查無資產趨勢數據。")
        return
        
    try:
        required_columns = ['日期', '總市值']
        if not all(col in trend_df.columns for col in required_columns):
            return
        
        trend_df = trend_df.copy()
        
        # 簡化日期處理
        trend_df['日期'] = pd.to_datetime(trend_df['日期'], errors='coerce')
        trend_df = trend_df.dropna(subset=['日期'])
        
        if trend_df.empty:
            return
        
        trend_df['總市值'] = trend_df['總市值'].apply(parse_number)
        trend_df = trend_df[trend_df['總市值'] > 0]
        
        if trend_df.empty:
            return
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['日期'], 
            y=trend_df['總市值'], 
            mode='lines+markers', 
            name='總市值',
            line=dict(color='#9CAF88', width=3),
            marker=dict(size=8, color='#7A8471')
        ))
        fig.update_layout(
            title='資產趨勢', 
            xaxis_title='日期', 
            yaxis_title='總市值 (NT$)',
            hovermode='x unified', 
            template="plotly_white",
            height=400,
            paper_bgcolor='rgba(253,252,247,0.9)',
            plot_bgcolor='rgba(253,252,247,0.9)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception:
        st.warning("資產趨勢圖載入失敗")

# 優化9: 主函數流程優化
def main():
    """主要應用程式邏輯 - 優化版本"""
    
    st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
    
    person = render_user_selection()
    
    # 優化：只在需要時顯示更新按鈕
    col1, col2, col3 = st.columns([1, 1, 8])
    with col2:
        if st.button('🔄 更新', key='refresh_button', help='清除快取並重新載入數據'):
            st.cache_data.clear()
            st.rerun()

    # 優化：條件式載入，只載入當前用戶的數據
    if person == 'asset_allocation':
        st.header("📊 整體資產配置分析")
        
        with st.spinner('正在計算資產配置...'):
            allocation_data, total_value, usd_twd_rate = get_asset_allocation_data()
        
        if total_value > 0:
            categories, target_percentages, actual_percentages, differences = render_asset_allocation_summary(
                allocation_data, total_value, usd_twd_rate
            