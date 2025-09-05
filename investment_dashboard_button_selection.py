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

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義CSS樣式 - 金融投資主題
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
        'holdings_range': '總覽與損益!A:H',
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'rita': {
        'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
        'holdings_range': '總覽與損益!A:H', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'ed': {
        'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
        'holdings_range': '總覽與損益!A:H', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B'
    },
    'ed_combined': {
        'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
        'schwab_range': 'schwab!A:Z',  # 取足夠的範圍確保包含B欄
        'cathay_range': '總覽與損益!A:Z'  # 取足夠的範圍確保包含F欄
    },
    'os': {
        'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
        'holdings_range': '總覽與損益!A:L'
    }
}

@st.cache_resource
def get_google_sheets_service():
    """取得Google Sheets服務實例"""
    try:
        # 從Streamlit secrets讀取憑證
        if "gcp_service_account" in st.secrets:
            credentials_info = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(credentials_info)
        else:
            st.error("找不到 gcp_service_account 設定在 Streamlit secrets 中")
            st.info("請在 Streamlit secrets 中設定 gcp_service_account 憑證")
            return None
        
        # 設置必要的權限範圍
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets.readonly'
        ])
        
        return build('sheets', 'v4', credentials=scoped_credentials)
    except Exception as e:
        st.error(f"Google Sheets API 設置失敗: {e}")
        st.info("請確認 gcp_service_account 在 Streamlit secrets 中設定正確")
        return None

def parse_number(value):
    """解析數字，處理各種格式"""
    if isinstance(value, (int, float)):
        return float(value)
    if not value or value == '':
        return 0.0
    
    # 移除逗號、百分號等符號
    cleaned = str(value).replace(',', '').replace('%', '').replace('"', '')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

@st.cache_data(ttl=600)  # 快取10分鐘，減少API呼叫
def load_sheet_data(person, data_type):
    """從Google Sheets載入數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        config = SHEET_CONFIGS[person]
        sheet_id = config['id']
        
        # 檢查是否為placeholder ID
        if sheet_id == 'PLACEHOLDER_ED_SHEET_ID':
            st.warning(f"請設定{person.upper()}的Google Sheets ID")
            return pd.DataFrame()
        
        if data_type == 'holdings':
            range_name = config['holdings_range']
        elif data_type == 'dca':
            range_name = config.get('dca_range')
        elif data_type == 'trend':
            range_name = config.get('trend_range')
        elif data_type == 'schwab':
            range_name = config.get('schwab_range')
        elif data_type == 'cathay':
            range_name = config.get('cathay_range')
        else:
            return pd.DataFrame()
        
        if not range_name:
            return pd.DataFrame()
        
        # 呼叫Google Sheets API
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        
        # 轉換為DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # 數據清理和轉換
        if person == 'os' and data_type == 'holdings':
            # 海外投資數據處理 - 根據實際column names調整
            # 移除debug用的column顯示
            
            # 根據可能的column名稱映射
            column_mapping = {
                '目前美價': 'current_price_usd',
                '總持有股數': 'total_shares', 
                '總投入成本(USD)': 'total_cost_usd',
                '目前總市值(USD)': 'current_value_usd',
                '目前總市值(NTD)': 'current_value_ntd',
                '未實現損益(USD)': 'unrealized_pl_usd',
                '未實現報酬率': 'return_rate',
                '投資損益(不計匯差,NTD)': 'investment_pl_ntd',
                '匯率損益(NTD)': 'fx_pl_ntd',
                '總未實現損益(計算匯差,NTD)': 'total_pl_ntd',
                '總未實現損益%': 'total_return_rate'
            }
            
            # 只處理實際存在的欄位
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率']):
                    numeric_columns.append(col)
            
        elif data_type == 'holdings':
            # 台股數據處理
            numeric_columns = [
                '總投入成本', '總持有股數', '目前股價', 
                '目前總市值', '未實現損益', '報酬率'
            ]
        elif data_type == 'dca':
            numeric_columns = ['每月投入金額', '扣款日', '券商折扣']
        elif data_type == 'trend':
            numeric_columns = ['總市值']
        elif data_type in ['schwab', 'cathay']:
            # 針對Ed的新頁籤數據處理
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率']):
                    numeric_columns.append(col)
        
        # 轉換數字欄位
        for col in numeric_columns:
            if col in df.columns:
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
        
        # 取得B欄(index 1)的所有數值
        b_column = schwab_df.iloc[:, 1]  # B欄
        
        # 找出最下方有數值的資料
        for i in range(len(b_column) - 1, -1, -1):
            value = b_column.iloc[i]
            if pd.notna(value) and str(value).strip() != '':
                parsed_value = parse_number(value)
                if parsed_value > 0:  # 確保是正值
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
        
        # 取得F欄(index 5)的所有數值
        f_column = cathay_df.iloc[:, 5]  # F欄
        
        total = 0.0
        for value in f_column:
            if pd.notna(value) and str(value).strip() != '':
                parsed_value = parse_number(value)
                if parsed_value > 0:  # 只加正值
                    total += parsed_value
        
        return total
    except Exception as e:
        st.error(f"計算國泰證券總市值失敗: {e}")
        return 0.0

def format_currency(amount, currency='TWD', show_prefix=True):
    """格式化貨幣"""
    if currency == 'USD':
        return f"${amount:,.0f}"
    else:
        if show_prefix:
            return f"NT${amount:,.0f}"
        else:
            return f"{amount:,.0f}"

def format_stock_price(price):
    """格式化股價 - 顯示到小數點第二位，不含NT$前綴"""
    return f"{price:.2f}"

def format_shares(shares):
    """格式化持股數 - 顯示到個位數"""
    return f"{shares:,.0f}"

def format_percentage(value):
    """格式化百分比"""
    return f"{'+' if value > 0 else ''}{value:.2f}%"

def render_user_selection():
    """渲染使用者選擇按鈕"""
    st.markdown("""
    <div class="user-selection-container">
    </div>
    """, unsafe_allow_html=True)
    
    # 使用者選項配置
    user_options = [
        {'key': 'jason', 'icon': '👨‍💼', 'label': 'Jason', 'desc': '台股投資'},
        {'key': 'rita', 'icon': '👩‍💼', 'label': 'Rita', 'desc': '台股投資'},
        {'key': 'ed', 'icon': '👨‍💻', 'label': 'Ed (台股)', 'desc': '台股投資'},
        {'key': 'ed_combined', 'icon': '🌐', 'label': 'Ed (美股)', 'desc': '嘉信+國泰美股'},
        {'key': 'os', 'icon': '🌍', 'label': '海外投資', 'desc': '富邦英股'}
    ]
    
    # 建立按鈕欄位
    cols = st.columns(len(user_options))
    
    # 初始化session state
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
    if person == 'os':
        # 海外投資摘要 - 動態處理欄位
        try:
            # 尋找對應的欄位名稱
            cost_col = None
            value_usd_col = None
            value_ntd_col = None
            pl_usd_col = None
            
            for col in holdings_df.columns:
                if '成本' in col and 'USD' in col:
                    cost_col = col
                elif '市值' in col and 'USD' in col:
                    value_usd_col = col
                elif '市值' in col and 'NTD' in col:
                    value_ntd_col = col
                elif '未實現' in col and 'USD' in col and '損益' in col:
                    pl_usd_col = col
            
            if not all([cost_col, value_usd_col]):
                st.error("海外投資數據欄位格式不符合預期")
                return
            
            total_cost_usd = holdings_df[cost_col].sum() if cost_col else 0
            total_value_usd = holdings_df[value_usd_col].sum() if value_usd_col else 0
            total_value_ntd = holdings_df[value_ntd_col].sum() if value_ntd_col else 0
            total_pl_usd = holdings_df[pl_usd_col].sum() if pl_usd_col else 0
            
            return_rate_usd = (total_pl_usd / total_cost_usd) * 100 if total_cost_usd > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">投資成本 (美元)</div>
                    <div class="metric-value">{format_currency(total_cost_usd, 'USD')}</div>
                    <div class="metric-change">持股檔數: {len(holdings_df)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">目前市值</div>
                    <div class="metric-value">{format_currency(total_value_usd, 'USD')}</div>
                    <div class="metric-change">{format_currency(total_value_ntd, 'TWD') if total_value_ntd else 'N/A'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                profit_class = 'profit' if total_pl_usd >= 0 else 'loss'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">投資損益 (美元)</div>
                    <div class="metric-value {profit_class}">{format_currency(total_pl_usd, 'USD')}</div>
                    <div class="metric-change {profit_class}">{format_percentage(return_rate_usd)}</div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"海外投資摘要卡片渲染錯誤: {e}")
            # 顯示可用欄位以供調試
            with st.expander("查看可用欄位 (調試用)"):
                st.write("Available columns:", holdings_df.columns.tolist())
    
    else:
        # 台股投資摘要
        total_cost = holdings_df['總投入成本'].sum()
        total_value = holdings_df['目前總市值'].sum()
        total_pl = holdings_df['未實現損益'].sum()
        total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">總投入成本</div>
                <div class="metric-value">{format_currency(total_cost)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">目前市值</div>
                <div class="metric-value">{format_currency(total_value)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            profit_class = 'profit' if total_pl >= 0 else 'loss'
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">未實現損益</div>
                <div class="metric-value {profit_class}">{format_currency(total_pl)}</div>
                <div class="metric-change {profit_class}">{format_percentage(total_return)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # 修正DCA卡片的HTML渲染問題 - 使用純Streamlit組件
            if dca_df is not None and not dca_df.empty:
                # 檢查必要的欄位是否存在
                required_dca_columns = ['股票代號', '股票名稱', '每月投入金額', '扣款日']
                if all(col in dca_df.columns for col in required_dca_columns):
                    # 使用純Streamlit的markdown和container來創建卡片效果
                    with st.container():
                        st.markdown("""
                        <div class="dca-card">
                            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 使用streamlit組件來顯示DCA項目
                        for _, row in dca_df.iterrows():
                            if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                                st.markdown(f"""
                                <div class="dca-item">
                                    <strong>{row["股票代號"]} {row["股票名稱"]}</strong><br>
                                    <small>每月{format_currency(row["每月投入金額"])} | {int(row["扣款日"])}號扣款</small>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="dca-card">
                        <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>
                        <div style="opacity: 0.8;">資料格式錯誤</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="dca-card">
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>
                    <div style="opacity: 0.8;">暫無設定資料</div>
                </div>
                """, unsafe_allow_html=True)

def render_ed_combined_summary(schwab_total_usd, cathay_total_usd):
    """渲染Ed綜合投資摘要卡片 - 全部使用USD計價"""
    
    total_combined = schwab_total_usd + cathay_total_usd
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="schwab-card">
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇺🇸 嘉信證券</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(schwab_total_usd, 'USD')}</div>
            <div style="opacity: 0.8;">美股個股總市值</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="cathay-card">
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇹🇼 國泰證券</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{format_currency(cathay_total_usd, 'USD')}</div>
            <div style="opacity: 0.8;">美股ETF總市值</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border: none; background: #e8f5e9;">
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #388e3c; opacity: 0.9;">總資產</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem;">{format_currency(total_combined, 'USD')}</div>
            <div style="opacity: 0.8;">嘉信 + 國泰</div>
        </div>
        """, unsafe_allow_html=True)

def render_holdings_table(holdings_df, person):
    """渲染持股表格"""
    if holdings_df.empty:
        st.info("查無持股數據。")
        return
    
    if person == 'os':
        # 海外投資表格
        # 重新命名欄位以便顯示
        display_df = holdings_df.rename(columns={
            '目前美價': '美價(USD)',
            '總持有股數': '股數',
            '總投入成本(USD)': '成本(USD)',
            '目前總市值(USD)': '市值(USD)',
            '未實現損益(USD)': '損益(USD)',
            '未實現報酬率': '報酬率%',
            '總未實現損益%': '總報酬率%'
        })
        
        # 選擇並排序要顯示的欄位
        display_columns = [
            '股票代號', '股票名稱', '美價(USD)', '股數', 
            '成本(USD)', '市值(USD)', '損益(USD)', '報酬率%'
        ]
        
        # 確保選取的欄位存在
        display_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[display_columns].style.format({
                '美價(USD)': "{:.2f}",
                '股數': "{:,.0f}",
                '成本(USD)': "${:,.0f}",
                '市值(USD)': "${:,.0f}",
                '損益(USD)': "${:,.0f}",
                '報酬率%': "{:,.2f}%"
            }),
            use_container_width=True
        )
        
    elif person == 'ed_combined':
        # Ed's綜合持股表格處理有所不同，此區塊用於jason, rita, ed
        # 合併schwab和cathay dfs如果需要，但提示顯示它們是分開的
        st.warning("Ed的詳細持股數據在此表格視圖中不支援。")

    else:
        # 台股投資表格
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
    
def render_portfolio_chart(holdings_df, person):
    """渲染投資組合圓餅圖和長條圖"""
    if holdings_df.empty:
        return
    
    if person == 'os':
        # 海外投資圖表
        try:
            # 找到市值欄位
            value_col = None
            for col in holdings_df.columns:
                if '市值' in col and 'USD' in col:
                    value_col = col
                    break
            
            if not value_col:
                st.warning("找不到市值欄位，無法繪製圖表。")
                return

            portfolio_df = holdings_df[['股票名稱', value_col]].copy()
            portfolio_df = portfolio_df[portfolio_df[value_col] > 0]
            
            fig = px.pie(
                portfolio_df, 
                values=value_col, 
                names='股票名稱', 
                title='資產配置 (按市值)',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"海外投資圖表繪製失敗: {e}")
            
    elif person == 'ed_combined':
        # Ed's綜合圖表
        st.warning("Ed的綜合投資組合圖表在此視圖中不支援。")
        
    else:
        # 台股投資圖表
        portfolio_df = holdings_df[['股票名稱', '目前總市值']].copy()
        portfolio_df = portfolio_df[portfolio_df['目前總市值'] > 0]
        
        fig = px.pie(
            portfolio_df, 
            values='目前總市值', 
            names='股票名稱', 
            title='資產配置 (按市值)',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Agsunset
        )
        fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
        st.plotly_chart(fig, use_container_width=True)
    
def render_trend_chart(trend_df):
    """渲染資產趨勢圖"""
    if trend_df.empty:
        st.info("查無資產趨勢數據。")
        return
    
    try:
        # 清理和轉換數據
        trend_df = trend_df.copy()
        trend_df['日期'] = pd.to_datetime(trend_df['日期'])
        trend_df['總市值'] = trend_df['總市值'].apply(parse_number)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['日期'], 
            y=trend_df['總市值'], 
            mode='lines+markers', 
            name='總市值',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8, color='#3498db', line=dict(width=1, color='DarkSlateGrey'))
        ))
        
        fig.update_layout(
            title='資產趨勢',
            xaxis_title='日期',
            yaxis_title='總市值 (NT$)',
            hovermode='x unified',
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"資產趨勢圖繪製失敗: {e}")
        st.write("數據預覽:", trend_df)

def main():
    """主要應用程式邏輯"""
    
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">📈 投資儀表板</h1>
        <p class="hero-subtitle">快速掌握個人資產概況與趨勢</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 使用者選擇
    person = render_user_selection()
    
    # 刷新按鈕
    if st.button('更新數據', key='refresh_button'):
        st.cache_data.clear()
        st.rerun()

    if person == 'ed_combined':
        st.header("Ed (綜合投資總覽)")
        
        # 載入數據
        schwab_df = load_sheet_data('ed_combined', 'schwab')
        cathay_df = load_sheet_data('ed_combined', 'cathay')

        # 處理並計算總值
        schwab_total_usd = get_schwab_total_value(schwab_df)
        cathay_total_usd = get_cathay_total_value(cathay_df)
        
        # 渲染摘要
        render_ed_combined_summary(schwab_total_usd, cathay_total_usd)
        
    else:
        st.header(f"{person.capitalize()} 投資總覽")

        # 載入數據
        holdings_df = load_sheet_data(person, 'holdings')
        dca_df = load_sheet_data(person, 'dca')
        trend_df = load_sheet_data(person, 'trend')

        if holdings_df.empty:
            st.warning("無法載入數據，請檢查Google Sheets設定和連線。")
        else:
            # 渲染摘要卡片
            render_summary_cards(person, holdings_df, dca_df)
            
            # 使用標籤頁組織內容
            tab1, tab2, tab3 = st.tabs(["📊 資產配置", "📈 損益表", "🗓️ 歷史趨勢"])
            
            with tab1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                render_portfolio_chart(holdings_df, person)
                st.markdown('</div>', unsafe_allow_html=True)

            with tab2:
                st.subheader("持股詳細列表")
                render_holdings_table(holdings_df, person)
            
            with tab3:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                render_trend_chart(trend_df)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
