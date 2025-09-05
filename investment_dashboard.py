def main():
    """主要應用程式邏輯"""
    
    st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
    
    person = render_user_selection()
    
    if st.button('更新數據', key='refresh_button'):
        st.cache_data.clear()
        st.rerun()

    if person == 'asset_allocation':
        st.header("🎯 資產配置總覽")
        
        asset_allocation, current_allocation, target_allocation, total_assets = render_asset_allocation_summary()
        
        if total_assets > 0:
            tab1, tab2, tab3 = st.tabs(["📊 配置分析", "📈 趨勢比較", "⚖️ 再平衡建議"])
            
            with tab1:
                st.subheader("資產配置現況分析")
                render_asset_allocation_charts(asset_allocation, current_allocation, target_allocation, total_assets)
            
            with tab2:
                st.subheader("配置趨勢比較")
                st.info("功能開發中 - 將顯示資產配置的歷史變化趨勢")
                
                # 顯示匯率影響提醒
                overseas_categories = ['美股個股', '美股ETF', '英股']
                overseas_total = sum([asset_allocation.get(cat, 0) for cat in overseas_categories])
                
                if overseas_total > 0:
                    st.warning(f"⚠️ 匯率提醒：目前海外資產總值約 {format_currency(overseas_total)} (依匯率 1 USD = {USD_TO_TWD_RATE} TWD 計算)")
            
            with tab3:
                st.subheader("再平衡建議")
                
                # 計算需要調整的金額
                rebalance_suggestions = []
                for category in set(list(current_allocation.keys()) + list(target_allocation.keys())):
                    current_pct = current_allocation.get(category, 0)
                    target_pct = target_allocation.get(category, 0)
                    
                    if abs(current_pct - target_pct) > 2:  # 偏差超過2%才建議調整
                        current_value = asset_allocation.get(category, 0)
                        target_value = total_assets * target_pct / 100
                        adjust_amount = target_value - current_value
                        
                        rebalance_suggestions.append({
                            '資產類別': category,
                            '目前配置%': f"{current_pct:.1f}%",
                            '目標配置%': f"{target_pct:.1f}%",
                            '建議調整': "買進" if adjust_amount > 0 else "賣出",
                            '調整金額': format_currency(abs(adjust_amount)),
                            '偏差程度': f"{current_pct - target_pct:+.1f}%"
                        })
                
                if rebalance_suggestions:
                    st.write("#### 建議調整項目：")
                    rebalance_df = pd.DataFrame(rebalance_suggestions)
                    st.dataframe(rebalance_df, use_container_width=True)
                    
                    st.info("💡 建議：優先調整偏差程度較大的資產類別，可透過定期定額方式逐步調整配置。")
                else:
                    st.success("✅ 目前各資產配置均在合理範圍內，無需大幅調整。")

    elif person == 'ed_overseas':
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
                st.write("##### ✏️ 新增一筆市值紀錄")
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
                
                # import streamlit as st
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
import time # 匯入 time 模組

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
    
    .allocation-card::before {
        content: '🎯';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 2rem;
        opacity: 0.3;
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
            'range': '總覽與損益!A:L'
        }
    },
    'allocation_config': {
        'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
        'range': '配置設定!A:Z'
    }
}

# USD/TWD匯率 (根據搜尋結果)
USD_TO_TWD_RATE = 30.72

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
        
        # --- 修改權限範圍 ---
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
        elif person == 'allocation_config':
            config = SHEET_CONFIGS[person]
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
        if not values:
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        
        if person == 'ed_overseas':
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率']):
                    numeric_columns.append(col)
        elif person == 'allocation_config':
            numeric_columns = ['目標配置%']
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

def get_asset_allocation_data():
    """取得並整理資產配置數據"""
    try:
        # 載入各個人的持股數據
        rita_df = load_sheet_data('rita', 'holdings')
        ed_df = load_sheet_data('ed', 'holdings')
        
        # 載入ED海外投資數據
        schwab_df = load_sheet_data('ed_overseas', None, 'schwab')
        cathay_df = load_sheet_data('ed_overseas', None, 'cathay')
        fubon_df = load_sheet_data('ed_overseas', None, 'fubon_uk')
        
        # 載入理想配置設定
        allocation_config_df = load_sheet_data('allocation_config', None)
        
        # 計算各類型資產的總值
        asset_allocation = {}
        
        # Rita台股投資
        if not rita_df.empty and '種類' in rita_df.columns:
            for _, row in rita_df.iterrows():
                category = row.get('種類', '').strip()
                if category:
                    market_value = parse_number(row.get('目前總市值', 0))
                    if category in asset_allocation:
                        asset_allocation[category] += market_value
                    else:
                        asset_allocation[category] = market_value
        
        # ED台股投資
        if not ed_df.empty and '種類' in ed_df.columns:
            for _, row in ed_df.iterrows():
                category = row.get('種類', '').strip()
                if category:
                    market_value = parse_number(row.get('目前總市值', 0))
                    if category in asset_allocation:
                        asset_allocation[category] += market_value
                    else:
                        asset_allocation[category] = market_value
        
        # ED海外投資 (轉換為台幣)
        # 嘉信證券 - 美股個股
        schwab_total_usd = get_schwab_total_value(schwab_df)
        if schwab_total_usd > 0:
            schwab_total_twd = schwab_total_usd * USD_TO_TWD_RATE
            if '美股個股' in asset_allocation:
                asset_allocation['美股個股'] += schwab_total_twd
            else:
                asset_allocation['美股個股'] = schwab_total_twd
        
        # 國泰證券 - 美股ETF
        cathay_total_usd = get_cathay_total_value(cathay_df)
        if cathay_total_usd > 0:
            cathay_total_twd = cathay_total_usd * USD_TO_TWD_RATE
            if '美股ETF' in asset_allocation:
                asset_allocation['美股ETF'] += cathay_total_twd
            else:
                asset_allocation['美股ETF'] = cathay_total_twd
        
        # 富邦英股 - 英股
        fubon_total_usd, _ = get_fubon_uk_total_value(fubon_df)
        if fubon_total_usd > 0:
            fubon_total_twd = fubon_total_usd * USD_TO_TWD_RATE
            if '英股' in asset_allocation:
                asset_allocation['英股'] += fubon_total_twd
            else:
                asset_allocation['英股'] = fubon_total_twd
        
        # 計算總資產
        total_assets = sum(asset_allocation.values())
        
        # 計算目前配置百分比
        current_allocation = {}
        for category, value in asset_allocation.items():
            current_allocation[category] = (value / total_assets * 100) if total_assets > 0 else 0
        
        # 整理理想配置
        target_allocation = {}
        if not allocation_config_df.empty and '資產類別' in allocation_config_df.columns and '目標配置%' in allocation_config_df.columns:
            for _, row in allocation_config_df.iterrows():
                category = row.get('資產類別', '').strip()
                target_pct = parse_number(row.get('目標配置%', 0))
                if category and target_pct > 0:
                    target_allocation[category] = target_pct
        
        return asset_allocation, current_allocation, target_allocation, total_assets