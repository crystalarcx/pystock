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

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義CSS樣式 - 金融投資主題 (樣式代碼與前一版本相同，此處省略以節省空間)
st.markdown("""
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
""", unsafe_allow_html=True)

# Google Sheets 配置
SHEET_CONFIGS = {
    'jason': {
        'id': '17qQIU4KMtbTpo_ozguuzKFHf1HHOhuEBanXxCyE8k4M',
        'holdings_range': '總覽與損益!A:I',
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B',
        'category_col': '類別' # 新增類別欄位名稱
    },
    'rita': {
        'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B',
        'category_col': '類別' # 新增類別欄位名稱
    },
    'ed': {
        'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B',
        'category_col': '類別' # 新增類別欄位名稱
    },
    'ed_overseas': {
        'schwab': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': 'schwab!A:Z',
            'category_col': '類別', # 新增類別欄位名稱
            'value_col': '目前總市值' # 新增市值欄位名稱
        },
        'cathay': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': '總覽與損益!A:Z',
            'category_col': '類別', # 新增類別欄位名稱
            'value_col': '目前總市值' # 新增市值欄位名稱
        },
        'fubon_uk': {
            'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
            'range': '總覽與損益!A:M',
            'category_col': '類別', # 新增類別欄位名稱
            'value_col': '目前總市值(USD)' # 新增市值欄位名稱
        }
    },
    'ideal_config': {
        'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
        'range': '配置設定!A:B'
    }
}

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
        
        # 將唯讀權限改為完整的讀寫權限
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets'
        ])
        
        return build('sheets', 'v4', credentials=scoped_credentials)
    except Exception as e:
        st.error(f"Google Sheets API 設置失敗: {e}")
        return None

# --- 新增函式：寫入資料到 Google Sheet ---
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
        # 使用 append 方法將資料加到工作表的最後一列
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED', # 讓 Google Sheets 自動解析資料格式 (如日期)
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"寫入 Google Sheets 失敗: {e}")
        return False
# --- 新增函式結束 ---

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

@st.cache_data(ttl=600)
def load_sheet_data(person, data_type, broker=None):
    """從Google Sheets載入數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        if person == 'ed_overseas':
            config = SHEET_CONFIGS[person][broker]
            sheet_id = config['id']
            range_name = config['range']
            category_col = config.get('category_col')
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
            category_col = config.get('category_col')
        
        if not range_name:
            return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        
        if person == 'ed_overseas':
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率']):
                    numeric_columns.append(col)
        elif data_type == 'holdings':
            numeric_columns = [
                '總投入成本', '總持有股數', '目前股價', 
                '目前總市值', '未實現損益', '報酬率'
            ]
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
        st.error(f"載入{person} {broker or data_type}數據失敗: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_ideal_config():
    """載入理想資產配置數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    config = SHEET_CONFIGS['ideal_config']
    sheet_id = config['id']
    range_name = config['range']

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df['理想百分比'] = df['理想百分比'].apply(parse_number)
        return df

    except Exception as e:
        st.error(f"載入理想配置數據失敗: {e}")
        return pd.DataFrame()

# 使用一個固定值或您可以自行實現獲取即時匯率的邏輯
@st.cache_data(ttl=3600)
def get_usd_twd_rate():
    """獲取美元兌台幣匯率"""
    # 由於無法直接呼叫外部套件，這裡使用固定值作為範例
    # 在實際部署時，您需要替換成可用的 API 或套件來獲取即時匯率
    st.info("無法獲取即時匯率，將使用固定匯率 32.5 作為示範。請自行替換此處的匯率獲取邏輯。")
    return 32.5

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

def format_currency(amount, currency='TWD', show_prefix=True):
    """格式化貨幣"""
    if currency == 'USD':
        return f"${amount:,.2f}" # 改為顯示兩位小數
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

def render_user_selection():
    """渲染使用者選擇按鈕"""
    st.markdown('<div class="user-selection-container"></div>', unsafe_allow_html=True)
    
    user_options = [
        {'key': 'jason', 'icon': '👨‍💼', 'label': 'Jason', 'desc': '台股投資'},
        {'key': 'rita', 'icon': '👩‍💼', 'label': 'Rita', 'desc': '台股投資'},
        {'key': 'ed', 'icon': '👨‍💻', 'label': 'Ed', 'desc': '台股投資'},
        {'key': 'ed_overseas', 'icon': '🌍', 'label': 'Ed', 'desc': '海外總覽'},
        {'key': 'combined', 'icon': '📊', 'label': '綜合', 'desc': '總資產配置'} # 新增綜合配置按鈕
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
    if person == 'ed_overseas':
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
            if dca_df is not None and not dca_df.empty:
                required_dca_columns = ['股票代號', '股票名稱', '每月投入金額', '扣款日']
                if all(col in dca_df.columns for col in required_dca_columns):
                    with st.container():
                        st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div></div>', unsafe_allow_html=True)
                        for _, row in dca_df.iterrows():
                            if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                                st.markdown(f'<div class="dca-item"><strong>{row["股票代號"]} {row["股票名稱"]}</strong><br><small>每月{format_currency(row["每月投入金額"])} | {int(row["扣款日"])}號扣款</small></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div><div style="opacity: 0.8;">資料格式錯誤</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="dca-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div><div style="opacity: 0.8;">暫無設定資料</div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"台股投資摘要卡片渲染錯誤: {e}")

def render_ed_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd, fubon_total_ntd):
    """渲染ED海外投資綜合摘要卡片"""
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

def render_holdings_table(holdings_df, person):
    if holdings_df.empty:
        st.info("查無持股數據。")
        return
    
    if person != 'ed_overseas':
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

def render_overseas_holdings_table(df, broker_name):
    if df.empty:
        st.info(f"查無{broker_name}持股數據。")
        return
    
    if broker_name == "富邦英股":
        display_df = df.rename(columns={
            '目前美價': '美價(USD)', '總持有股數': '股數',
            '總投入成本(USD)': '成本(USD)', '目前總市值(USD)': '市值(USD)',
            '未實現損益(USD)': '損益(USD)', '未實現報酬率': '報酬率%',
            '總未實現損益%': '總報酬率%'
        })
        display_columns = [
            '股票代號', '股票名稱', '美價(USD)', '股數', 
            '成本(USD)', '市值(USD)', '損益(USD)', '報酬率%'
        ]
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
    
def render_portfolio_chart(holdings_df, person):
    if holdings_df.empty: return
    if person != 'ed_overseas':
        portfolio_df = holdings_df[['股票名稱', '目前總市值']].copy()
        portfolio_df = portfolio_df[portfolio_df['目前總市值'] > 0]
        fig = px.pie(
            portfolio_df, values='目前總市值', names='股票名稱', 
            title='資產配置 (按市值)', hole=0.4,
            color_discrete_sequence=px.colors.sequential.Agsunset
        )
        fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
        st.plotly_chart(fig, use_container_width=True)

def render_overseas_portfolio_chart(df, broker_name):
    if df.empty: return
    try:
        value_col, name_col = None, None
        for col in df.columns:
            if '市值' in col and ('USD' in col or 'NTD' not in col): value_col = col; break
        for col in df.columns:
            if '名稱' in col: name_col = col; break
        if not value_col or not name_col:
            st.warning(f"找不到{broker_name}的市值或名稱欄位，無法繪製圖表。"); return
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
    
def render_trend_chart(trend_df):
    if trend_df.empty:
        st.info("查無資產趨勢數據。"); return
    try:
        trend_df = trend_df.copy()
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
        st.error(f"資產趨勢圖繪製失敗: {e}"); st.write("數據預覽:", trend_df)

def render_combined_portfolio_page():
    """渲染綜合資產配置頁面"""
    st.header("📊 綜合資產配置總覽")

    # 1. 載入所有相關數據
    rita_df = load_sheet_data('rita', 'holdings')
    ed_tw_df = load_sheet_data('ed', 'holdings')
    ed_schwab_df = load_sheet_data('ed_overseas', None, 'schwab')
    ed_cathay_df = load_sheet_data('ed_overseas', None, 'cathay')
    ed_fubon_df = load_sheet_data('ed_overseas', None, 'fubon_uk')
    ideal_df = load_ideal_config()

    usd_twd_rate = get_usd_twd_rate()
    st.info(f"當前美元兌台幣匯率：1 USD = {usd_twd_rate:.2f} TWD")

    combined_df = pd.DataFrame()

    # 2. 處理 Rita 的台股數據
    if not rita_df.empty and '目前總市值' in rita_df.columns and '類別' in rita_df.columns:
        rita_df = rita_df[['類別', '目前總市值']].rename(columns={'目前總市值': '總市值(NTD)'})
        combined_df = pd.concat([combined_df, rita_df], ignore_index=True)

    # 3. 處理 Ed 的台股數據
    if not ed_tw_df.empty and '目前總市值' in ed_tw_df.columns and '類別' in ed_tw_df.columns:
        ed_tw_df = ed_tw_df[['類別', '目前總市值']].rename(columns={'目前總市值': '總市值(NTD)'})
        combined_df = pd.concat([combined_df, ed_tw_df], ignore_index=True)

    # 4. 處理 Ed 的海外數據 (USD 換算成 TWD)
    if not ed_schwab_df.empty and '目前總市值' in ed_schwab_df.columns and '類別' in ed_schwab_df.columns:
        ed_schwab_df['總市值(NTD)'] = ed_schwab_df['目前總市值'] * usd_twd_rate
        ed_schwab_df = ed_schwab_df[['類別', '總市值(NTD)']]
        combined_df = pd.concat([combined_df, ed_schwab_df], ignore_index=True)

    if not ed_cathay_df.empty and '目前總市值' in ed_cathay_df.columns and '類別' in ed_cathay_df.columns:
        ed_cathay_df['總市值(NTD)'] = ed_cathay_df['目前總市值'] * usd_twd_rate
        ed_cathay_df = ed_cathay_df[['類別', '總市值(NTD)']]
        combined_df = pd.concat([combined_df, ed_cathay_df], ignore_index=True)

    if not ed_fubon_df.empty and '目前總市值(USD)' in ed_fubon_df.columns and '類別' in ed_fubon_df.columns:
        ed_fubon_df['總市值(NTD)'] = ed_fubon_df['目前總市值(USD)'] * usd_twd_rate
        ed_fubon_df = ed_fubon_df[['類別', '總市值(NTD)']]
        combined_df = pd.concat([combined_df, ed_fubon_df], ignore_index=True)

    # 5. 計算目前資產配置
    if combined_df.empty or '總市值(NTD)' not in combined_df.columns:
        st.warning("無法載入綜合資產配置數據，或數據格式有誤。")
        return
    
    current_portfolio = combined_df.groupby('類別')['總市值(NTD)'].sum().reset_index()
    total_value = current_portfolio['總市值(NTD)'].sum()
    if total_value > 0:
        current_portfolio['目前百分比'] = (current_portfolio['總市值(NTD)'] / total_value) * 100
    else:
        current_portfolio['目前百分比'] = 0

    # 6. 整理數據並與理想配置合併
    if not ideal_df.empty and '資產類別' in ideal_df.columns and '理想百分比' in ideal_df.columns:
        ideal_df = ideal_df.rename(columns={'資產類別': '類別'})
        final_df = pd.merge(current_portfolio, ideal_df, on='類別', how='outer').fillna(0)
    else:
        st.warning("無法載入理想資產配置數據，將只顯示目前配置。")
        final_df = current_portfolio.rename(columns={'目前百分比': '理想百分比'})
        final_df['差異'] = 0
        final_df['理想百分比'] = 0

    if '理想百分比' in final_df.columns:
        final_df['差異'] = final_df['目前百分比'] - final_df['理想百分比']
        final_df['建議調整'] = final_df['差異'].apply(lambda x: '超配' if x > 0 else ('低配' if x < 0 else '符合'))
    else:
        final_df['差異'] = 0
        final_df['建議調整'] = '無'
    
    final_df['總市值(NTD)'] = final_df['總市值(NTD)'].apply(lambda x: f"NT${x:,.0f}")
    final_df['目前百分比'] = final_df['目前百分比'].apply(lambda x: f"{x:,.2f}%")
    if '理想百分比' in final_df.columns:
        final_df['理想百分比'] = final_df['理想百分比'].apply(lambda x: f"{x:,.2f}%")
        final_df['差異'] = final_df['差異'].apply(lambda x: f"{x:+.2f}%")

    # 7. 繪製圖表與表格
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("目前資產配置")
        if not current_portfolio.empty and total_value > 0:
            fig_current = px.pie(
                current_portfolio, values='總市值(NTD)', names='類別',
                title=f'總資產市值: {format_currency(total_value)}', hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_current.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_current, use_container_width=True)
        else:
            st.info("查無目前資產配置數據。")

    with col2:
        st.subheader("理想資產配置")
        if not ideal_df.empty and '理想百分比' in ideal_df.columns:
            fig_ideal = px.pie(
                ideal_df, values='理想百分比', names='類別',
                title='理想配置', hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_ideal.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_ideal, use_container_width=True)
        else:
            st.info("查無理想配置數據。")

    st.subheader("配置差異明細")
    if '差異' in final_df.columns:
        st.dataframe(final_df[['類別', '總市值(NTD)', '目前百分比', '理想百分比', '差異', '建議調整']], use_container_width=True)
    else:
        st.dataframe(final_df[['類別', '總市值(NTD)', '目前百分比']], use_container_width=True)
    
def main():
    """主要應用程式邏輯"""
    
    st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
    
    person = render_user_selection()
    
    if st.button('更新數據', key='refresh_button'):
        st.cache_data.clear()
        st.rerun()

    if person == 'ed_overseas':
        st.header("Ed 海外投資總覽")
        
        schwab_df = load_sheet_data('ed_overseas', None, 'schwab')
        cathay_df = load_sheet_data('ed_overseas', None, 'cathay')
        fubon_df = load_sheet_data('ed_overseas', None, 'fubon_uk')

        schwab_total_usd = get_schwab_total_value(schwab_df)
        cathay_total_usd = get_cathay_total_value(cathay_df)
        fubon_total_usd, fubon_total_ntd = get_fubon_uk_total_value(fubon_df)
        
        render_ed_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd, fubon_total_ntd)
        
        tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 嘉信證券", "🇹🇼 國泰證券", "🇬🇧 富邦英股", "📊 綜合分析"])
        
        with tab1:
            st.subheader("嘉信證券 - 美股個股")
            
            # --- 新增寫入功能區塊 ---
            with st.form("schwab_append_form", clear_on_submit=True):
                st.write("##### ✍️ 新增一筆市值紀錄")
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    record_date = st.date_input("紀錄日期", value=datetime.now())
                with c2:
                    market_value = st.number_input("總市值 (USD)", min_value=0.0, format="%.2f")
                with c3:
                    st.write("") # 用於對齊按鈕
                    st.write("") # 用於對齊按鈕
                    submitted = st.form_submit_button("新增至 Google Sheet")

            if submitted:
                # 取得工作表ID和名稱
                sheet_id = SHEET_CONFIGS['ed_overseas']['schwab']['id']
                worksheet_name = 'schwab' # append API 只需要工作表名稱
                
                # 格式化準備寫入的資料
                date_str = record_date.strftime('%Y/%m/%d')
                values_to_append = [[date_str, market_value]]
                
                # 呼叫寫入函式
                success = append_to_sheet(sheet_id, worksheet_name, values_to_append)
                
                if success:
                    st.success("紀錄已成功新增！正在重新整理數據...")
                    time.sleep(1) # 暫停1秒讓使用者看到成功訊息
                    st.cache_data.clear() # 清除資料快取
                    st.rerun() # 重新執行程式以讀取新資料
                else:
                    st.error("新增紀錄失敗，請檢查後台日誌或 API 權限。")
            
            st.divider()
            # --- 寫入功能區塊結束 ---

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                render_overseas_portfolio_chart(schwab_df, "嘉信證券")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                render_overseas_holdings_table(schwab_df, "嘉信證券")

        with tab2:
            st.subheader("國泰證券 - 美股ETF")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                render_overseas_portfolio_chart(cathay_df, "國泰證券")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                render_overseas_holdings_table(cathay_df, "國泰證券")
        
        with tab3:
            st.subheader("富邦證券 - 英股投資")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                render_overseas_portfolio_chart(fubon_df, "富邦英股")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                render_overseas_holdings_table(fubon_df, "富邦英股")
        
        with tab4:
            st.subheader("綜合投資分析")
            platforms = ['嘉信證券', '國泰證券', '富邦英股']
            values = [schwab_total_usd, cathay_total_usd, fubon_total_usd]
            
            fig = px.bar(
                x=platforms, y=values, title='各平台投資總值比較 (USD)',
                color=platforms, color_discrete_sequence=['#1f4e79', '#8b0000', '#2d3436']
            )
            fig.update_layout(showlegend=False, yaxis_title='總市值 (USD)')
            st.plotly_chart(fig, use_container_width=True)
    elif person == 'combined':
        render_combined_portfolio_page()
    else:
        st.header(f"{person.capitalize()} 台股投資總覽")
        
        holdings_df = load_sheet_data(person, 'holdings')
        dca_df = load_sheet_data(person, 'dca')
        trend_df = load_sheet_data(person, 'trend')

        if not holdings_df.empty:
            render_summary_cards(person, holdings_df, dca_df)
            tab1, tab2, tab3 = st.tabs(["📈 持股明細", "🥧 資產配置", "📊 資產趨勢"])
            with tab1:
                st.subheader("持股明細")
                render_holdings_table(holdings_df, person)
            with tab2:
                st.subheader("資產配置")
                render_portfolio_chart(holdings_df, person)
            with tab3:
                st.subheader("資產趨勢")
                render_trend_chart(trend_df)
        else:
            st.warning(f"無法載入 {person} 的投資數據，或數據為空。")

if __name__ == "__main__":
    main()
