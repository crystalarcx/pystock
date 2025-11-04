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
import twstock

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .main > div { padding-top: 1rem; }
    .css-1d391kg { display: none; }
    
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
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        border: 1px solid rgba(0,0,0,0.05);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
        position: relative;
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
    
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
    }
    
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
    
    .trading-form-container {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 2px solid rgba(52, 152, 219, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .trading-form-title {
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .notes-container {
        background: linear-gradient(135deg, #fff5e6, #ffe8cc);
        border: 2px solid rgba(243, 156, 18, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .notes-title {
        color: #e67e22;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .note-item {
        background: white;
        border-left: 4px solid #f39c12;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease;
    }
    
    .note-item:hover {
        transform: translateX(5px);
    }
    
    .note-date {
        color: #7f8c8d;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .note-content {
        color: #2c3e50;
        font-size: 0.95rem;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 1.8rem; }
        .hero-section { padding: 1.5rem 1rem; }
        .metric-card { padding: 1.2rem; }
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
        'notes_range': 'notes!A:B'
    },
    'rita': {
        'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B',
        'trading_records_range': '交易紀錄!A:G',
        'notes_range': 'notes!A:B'
    },
    'ed': {
        'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
        'holdings_range': '總覽與損益!A:I', 
        'dca_range': '投資設定!A:E',
        'trend_range': '資產趨勢!A:B',
        'notes_range': 'notes!A:B'
    },
    'ed_overseas': {
        'schwab': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': 'schwab!A:Z'
        },
        'cathay': {
            'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
            'range': '總覽與損益!A:Z',
            'dca_range': '投資設定!A:E'
        },
        'fubon_uk': {
            'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
            'range': '總覽與損益!A:M'
        }
    }
}

# 目標配置設定
TARGET_ALLOCATION = {
    '美股ETF': 40,
    '美股個股': 25,
    '台股ETF': 20,
    '台股個股': 15,
    '美債ETF': 0,
    '黃金ETF': 0
}

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
    except Exception as e:
        return 31.0

@st.cache_data
def parse_number(value):
    """解析數字,處理各種格式"""
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

@st.cache_data(ttl=3600)
def get_stock_name(stock_code):
    """使用 twstock 取得股票名稱"""
    try:
        realtime_data = twstock.realtime.get(stock_code)
        if realtime_data and realtime_data.get('success', False):
            return realtime_data['info']['name']
        else:
            return f"股票{stock_code}"
    except Exception as e:
        st.warning(f"無法取得股票 {stock_code} 的名稱: {e}")
        return f"股票{stock_code}"

def get_next_row_number(sheet_id, range_name):
    """獲取工作表的下一行號"""
    try:
        service = get_google_sheets_service()
        if not service:
            return None
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        return len(values) + 1
        
    except Exception as e:
        st.error(f"獲取行號失敗: {e}")
        return None

def process_trading_record(person, stock_code, stock_price, stock_quantity, transaction_type, holding_type, transaction_date):
    """處理交易記錄邏輯"""
    try:
        sheet_id = SHEET_CONFIGS[person]['id']
        
        if transaction_type == "買進":
            total_amount = stock_price * stock_quantity
            final_quantity = stock_quantity
        else:
            total_amount = stock_price * stock_quantity * (-1)
            final_quantity = stock_quantity * (-1)
        
        trading_record_values = [[
            transaction_date.strftime('%Y/%m/%d'),
            stock_code,
            stock_price,
            '',
            '',
            total_amount,
            final_quantity
        ]]
        
        success = append_to_sheet(sheet_id, '交易紀錄', trading_record_values)
        
        if not success:
            return False
        
        if holding_type == "新持有" and transaction_type == "買進":
            stock_name = get_stock_name(stock_code)
            next_row = get_next_row_number(sheet_id, '總覽與損益!A:A')
            if next_row is None:
                next_row = 2
            
            holdings_values = [[
                stock_code,
                stock_name,
                f'=IF(ISBLANK(A{next_row}), "", SUMIF(\'交易紀錄\'!B:B, A{next_row}, \'交易紀錄\'!F:F))',
                f'=IF(ISBLANK(A{next_row}), "", SUMIF(\'交易紀錄\'!B:B, A{next_row}, \'交易紀錄\'!G:G))',
                f'=IF(ISBLANK(A{next_row}), "", GOOGLEFINANCE("TPE:" & A{next_row}, "price"))',
                f'=IF(ISBLANK(A{next_row}), "", D{next_row}*E{next_row})',
                f'=IF(ISBLANK(A{next_row}), "", F{next_row}-C{next_row})',
                f'=IF(ISBLANK(A{next_row}), "", G{next_row}/C{next_row})'
            ]]
            
            success = append_to_sheet(sheet_id, '總覽與損益', holdings_values)
            
        return success
        
    except Exception as e:
        st.error(f"處理交易記錄時發生錯誤: {e}")
        return False

def render_trading_form_for_person(person):
    """渲染交易記錄輸入表單"""
    st.markdown('<div class="trading-form-container">', unsafe_allow_html=True)
    st.markdown('<div class="trading-form-title">📝 新增交易記錄</div>', unsafe_allow_html=True)
    
    if 'trading_form_data' not in st.session_state:
        st.session_state.trading_form_data = {
            'holding_type': '原本持有',
            'transaction_type': '買進',
            'stock_code': '',
            'stock_price': 100.0,
            'stock_quantity': 1000
        }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**持股狀態 (必選)**")
        holding_type = st.radio(
            "",
            ["原本持有", "新持有"],
            key="holding_type_radio",
            horizontal=True,
            index=0 if st.session_state.trading_form_data['holding_type'] == '原本持有' else 1
        )
        st.session_state.trading_form_data['holding_type'] = holding_type
    
    with col2:
        st.write("**交易類型 (必選)**")
        transaction_type = st.radio(
            "",
            ["買進", "賣出"],
            key="transaction_type_radio",
            horizontal=True,
            index=0 if st.session_state.trading_form_data['transaction_type'] == '買進' else 1
        )
        if transaction_type != st.session_state.trading_form_data['transaction_type']:
            st.session_state.trading_form_data['transaction_type'] = transaction_type
            st.session_state.trading_form_data['stock_quantity'] = 1000
    
    st.divider()
    
    col3, col4, col5, col6 = st.columns(4)
    
    with col3:
        transaction_date = st.date_input(
            "交易日期",
            value=datetime.now(),
            key="transaction_date_input"
        )
    
    with col4:
        stock_code = st.text_input(
            "股票代號",
            placeholder="例如: 2330",
            key="stock_code_input",
            value=st.session_state.trading_form_data['stock_code']
        )
        st.session_state.trading_form_data['stock_code'] = stock_code
    
    with col5:
        stock_price = st.number_input(
            "股價",
            min_value=0.01,
            value=st.session_state.trading_form_data['stock_price'],
            step=0.01,
            format="%.2f",
            key="stock_price_input"
        )
        st.session_state.trading_form_data['stock_price'] = stock_price
    
    with col6:
        stock_quantity = st.number_input(
            "股數",
            value=st.session_state.trading_form_data['stock_quantity'],
            step=1000,
            min_value=1,
            key="stock_quantity_input"
        )
        st.session_state.trading_form_data['stock_quantity'] = stock_quantity
    
    st.divider()
    
    if transaction_type == "買進":
        total_amount = stock_price * stock_quantity
        final_quantity = stock_quantity
    else:
        total_amount = stock_price * stock_quantity * (-1)
        final_quantity = stock_quantity * (-1)
    
    col7, col8, col9 = st.columns(3)
    with col7:
        st.info(f"**交易金額:** NT${total_amount:,.0f}")
    with col8:
        st.info(f"**最終股數:** {final_quantity:,}")
    with col9:
        if holding_type == "新持有" and transaction_type == "買進":
            st.success("**將同時新增至持股清單**")
        else:
            st.info("**僅記錄交易**")
    
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button(
            "✅ 確定",
            use_container_width=True,
            type="primary",
            key="submit_trading_record"
        ):
            if not stock_code:
                st.error("請輸入股票代號!")
            elif stock_quantity <= 0:
                st.error("股數必須大於零!")
            else:
                with st.spinner('正在處理交易記錄...'):
                    success = process_trading_record(
                        person=person,
                        stock_code=stock_code,
                        stock_price=stock_price,
                        stock_quantity=stock_quantity,
                        transaction_type=transaction_type,
                        holding_type=holding_type,
                        transaction_date=transaction_date
                    )
                
                if success:
                    st.success("✅ 交易記錄已成功新增!")
                    if holding_type == "新持有" and transaction_type == "買進":
                        st.success(f"✅ 股票 {stock_code} 已新增至持股清單!")
                    
                    st.session_state.trading_form_data = {
                        'holding_type': '原本持有',
                        'transaction_type': '買進',
                        'stock_code': '',
                        'stock_price': 100.0,
                        'stock_quantity': 1000
                    }
                    
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ 交易記錄新增失敗,請檢查網路連線或權限設定。")
    
    st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data(ttl=1800)
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
        
        max_cols = len(values[0]) if values else 0
        normalized_values = [row + [''] * (max_cols - len(row)) for row in values]
        
        df = pd.DataFrame(normalized_values[1:], columns=normalized_values[0])
        df = df.dropna(how='all')
        
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

@st.cache_data(ttl=600)
def load_notes_data(person):
    """載入投資筆記數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
        config = SHEET_CONFIGS[person]
        sheet_id = config['id']
        range_name = config.get('notes_range')
        
        if not range_name:
            return pd.DataFrame()
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        
        max_cols = len(values[0]) if values else 0
        normalized_values = [row + [''] * (max_cols - len(row)) for row in values]
        
        df = pd.DataFrame(normalized_values[1:], columns=normalized_values[0])
        df = df.dropna(how='all')
        
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"載入{person}筆記失敗: {str(e)}")
        return pd.DataFrame()

def save_note(person, note_content):
    """儲存筆記到 Google Sheets"""
    try:
        sheet_id = SHEET_CONFIGS[person]['id']
        current_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        values_to_append = [[current_date, note_content]]
        
        success = append_to_sheet(sheet_id, 'notes', values_to_append)
        
        return success
        
    except Exception as e:
        st.error(f"儲存筆記失敗: {e}")
        return False

def render_notes_section(person, notes_df):
    """渲染筆記功能區塊"""
    st.markdown('<div class="notes-container">', unsafe_allow_html=True)
    st.markdown('<div class="notes-title">📝 投資筆記</div>', unsafe_allow_html=True)
    
    with st.form(key=f"note_form_{person}", clear_on_submit=True):
        st.write("##### ✍️ 新增筆記")
        note_content = st.text_area(
            "筆記內容",
            placeholder="記錄你的投資想法、市場觀察、交易原因...",
            height=120,
            key=f"note_content_{person}"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("💾 儲存筆記", use_container_width=True, type="primary")
        
        if submitted:
            if not note_content or note_content.strip() == "":
                st.error("❌ 筆記內容不能為空!")
            else:
                with st.spinner('正在儲存筆記...'):
                    success = save_note(person, note_content.strip())
                
                if success:
                    st.success("✅ 筆記已成功儲存!")
