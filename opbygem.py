# optimized_settlement.py
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# 頁面配置
st.set_page_config(
    page_title="投資總覽",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 1. 配置管理模組 (Config Module)
# ==============================================================================
class AppConfig:
    """應用程式靜態配置管理"""

    # Streamlit CSS樣式
    STYLE_CSS = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main > div { padding-top: 1rem; }
        .css-1d391kg { display: none; }
        .hero-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem 2rem; border-radius: 20px; margin-bottom: 2rem; text-align: center; box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3); position: relative; overflow: hidden; }
        .hero-section::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat; animation: float 20s ease-in-out infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        .hero-title { font-size: 3rem; font-weight: 700; margin: 0; text-shadow: 2px 2px 8px rgba(0,0,0,0.3); position: relative; z-index: 1; }
        .hero-subtitle { font-size: 1.2rem; margin: 1rem 0 0 0; opacity: 0.95; position: relative; z-index: 1; }
        .user-selection-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin: 2rem 0; padding: 2rem; background: rgba(255, 255, 255, 0.05); border-radius: 20px; backdrop-filter: blur(10px); }
        .user-btn { background: linear-gradient(135deg, #ffffff, #f8f9fa); color: #2c3e50; border: 2px solid rgba(52, 152, 219, 0.2); border-radius: 15px; padding: 20px 30px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; text-decoration: none; display: flex; flex-direction: column; align-items: center; min-width: 150px; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); position: relative; overflow: hidden; }
        .user-btn:before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent); transition: left 0.5s; }
        .user-btn:hover:before { left: 100%; }
        .user-btn:hover { transform: translateY(-8px); box-shadow: 0 15px 35px rgba(52, 152, 219, 0.3); border-color: #3498db; }
        .user-btn.active { background: linear-gradient(135deg, #3498db, #2980b9); color: white; border-color: #3498db; transform: translateY(-5px); box-shadow: 0 12px 30px rgba(52, 152, 219, 0.4); }
        .user-btn-icon { font-size: 2rem; margin-bottom: 8px; }
        .user-btn-label { font-size: 1rem; font-weight: 600; }
        .user-btn-desc { font-size: 0.8rem; opacity: 0.7; margin-top: 4px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(248, 249, 250, 0.8); padding: 8px; border-radius: 12px; backdrop-filter: blur(10px); }
        .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; padding: 16px 32px; color: #6c757d; font-weight: 600; font-size: 1rem; transition: all 0.3s ease; border: none; }
        .stTabs [data-baseweb="tab"]:hover { background: rgba(52, 152, 219, 0.1); color: #3498db; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #3498db, #2980b9) !important; color: white !important; box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4); }
        .metric-card { background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid rgba(0,0,0,0.05); padding: 2rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); text-align: center; margin-bottom: 1.5rem; transition: transform 0.3s ease, box-shadow 0.3s ease; position: relative; overflow: hidden; }
        .metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c, #f39c12); }
        .metric-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12); }
        .metric-value { font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: #2c3e50; }
        .metric-label { font-size: 1rem; color: #7f8c8d; font-weight: 500; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-change { font-size: 0.9rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; display: inline-block; }
        .profit { color: #27ae60; background: rgba(39, 174, 96, 0.1); }
        .loss { color: #e74c3c; background: rgba(231, 76, 60, 0.1); }
        .dca-card { background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 2rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(243, 156, 18, 0.3); margin-bottom: 1.5rem; position: relative; overflow: hidden; }
        .dca-card::before { content: '📊'; position: absolute; top: 1rem; right: 1rem; font-size: 2rem; opacity: 0.3; }
        .dca-item { background: rgba(255, 255, 255, 0.15); border-radius: 12px; padding: 16px; margin-bottom: 12px; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); transition: all 0.3s ease; }
        .dca-item:hover { background: rgba(255, 255, 255, 0.25); transform: translateX(5px); }
        .schwab-card { background: linear-gradient(135deg, #1f4e79, #2e6da4); color: white; padding: 2rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(31, 78, 121, 0.3); margin-bottom: 1.5rem; position: relative; overflow: hidden; }
        .cathay-card { background: linear-gradient(135deg, #8b0000, #dc143c); color: white; padding: 2rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(139, 0, 0, 0.3); margin-bottom: 1.5rem; position: relative; overflow: hidden; }
        .fubon-card { background: linear-gradient(135deg, #2d3436, #636e72); color: white; padding: 2rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(45, 52, 54, 0.3); margin-bottom: 1.5rem; position: relative; overflow: hidden; }
        .allocation-card { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 2rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(108, 92, 231, 0.3); margin-bottom: 1.5rem; position: relative; overflow: hidden; }
        .chart-container { background: white; border-radius: 16px; padding: 1.5rem; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); margin-bottom: 2rem; border: 1px solid rgba(0,0,0,0.05); }
        .dataframe { border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); }
        .stButton > button { background: linear-gradient(135deg, #3498db, #2980b9); color: white; border: none; border-radius: 10px; padding: 0.5rem 1.5rem; font-weight: 600; transition: all 0.3s ease; box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3); }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(52, 152, 219, 0.4); }
        @media (max-width: 768px) { .hero-title { font-size: 2rem; } .hero-section { padding: 2rem 1rem; } .metric-card { padding: 1.5rem; } .user-selection-container { flex-direction: column; align-items: center; } .user-btn { min-width: 200px; } }
    </style>
    """
    
    # Google Sheets 配置
    SHEET_CONFIGS = {
        'jason': { 'id': '17qQIU4KMtbTpo_ozguuzKFHf1HHOhuEBanXxCyE8k4M', 'holdings_range': '總覽與損益!A:I', 'dca_range': '投資設定!A:E', 'trend_range': '資產趨勢!A:B' },
        'rita': { 'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw', 'holdings_range': '總覽與損益!A:I', 'dca_range': '投資設定!A:E', 'trend_range': '資產趨勢!A:B' },
        'ed': { 'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc', 'holdings_range': '總覽與損益!A:I', 'dca_range': '投資設定!A:E', 'trend_range': '資產趨勢!A:B' },
        'ed_overseas': {
            'schwab': { 'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0', 'range': 'schwab!A:Z' },
            'cathay': { 'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0', 'range': '總覽與損益!A:Z' },
            'fubon_uk': { 'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA', 'range': '總覽與損益!A:M' }
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

    # 用戶選項
    USER_OPTIONS = [
        {'key': 'jason', 'icon': '👨‍💼', 'label': 'Jason', 'desc': '台股投資'},
        {'key': 'rita', 'icon': '👩‍💼', 'label': 'Rita', 'desc': '台股投資'},
        {'key': 'ed', 'icon': '👨‍💻', 'label': 'Ed', 'desc': '台股投資'},
        {'key': 'ed_overseas', 'icon': '🌐', 'label': 'Ed', 'desc': '海外總覽'},
        {'key': 'asset_allocation', 'icon': '📊', 'label': '資產配置', 'desc': '整體配置'}
    ]

# ==============================================================================
# 2. 數據處理與載入模組 (Data Loader Module)
# ==============================================================================
class DataLoader:
    """處理數據載入、解析與快取邏輯"""

    @staticmethod
    @st.cache_resource
    def get_google_sheets_service():
        """取得 Google Sheets 服務實例並快取"""
        try:
            if "gcp_service_account" in st.secrets:
                credentials_info = dict(st.secrets["gcp_service_account"])
                credentials = Credentials.from_service_account_info(credentials_info)
            else:
                st.error("找不到 gcp_service_account 設定在 Streamlit secrets 中")
                return None
            
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/spreadsheets'])
            return build('sheets', 'v4', credentials=scoped_credentials)
        except Exception as e:
            st.error(f"Google Sheets API 設置失敗: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=3600)  # 快取1小時，減少API調用
    def get_usd_twd_rate():
        """取得 USDTWD 匯率，帶有重試機制和優雅降級"""
        try:
            for i in range(3): # 重試3次
                try:
                    ticker = yf.Ticker("USDTWD=X")
                    data = ticker.history(period="1d")
                    if not data.empty:
                        return data['Close'].iloc[-1]
                except Exception:
                    time.sleep(1) # 重試前等待
            st.warning("無法獲得即時匯率，使用預設值 31.0")
            return 31.0
        except Exception as e:
            st.warning(f"無法獲得即時匯率: {e}，使用預設值 31.0")
            return 31.0

    @staticmethod
    def parse_number(value):
        """解析數字，處理各種格式"""
        if isinstance(value, (int, float)):
            return float(value)
        if not value or str(value).strip() == '':
            return 0.0
        
        cleaned = str(value).replace(',', '').replace('%', '').replace('"', '')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    @st.cache_data(ttl=600, show_spinner="正在從 Google Sheets 載入數據...")
    def load_sheet_data(person, data_type, broker=None):
        """從Google Sheets載入數據，並加入錯誤處理與數據驗證"""
        service = DataLoader.get_google_sheets_service()
        if not service:
            return pd.DataFrame()
        
        try:
            config = AppConfig.SHEET_CONFIGS.get(person)
            if not config:
                st.error(f"找不到 '{person}' 的配置。")
                return pd.DataFrame()
            
            if person == 'ed_overseas':
                broker_config = config.get(broker)
                if not broker_config:
                    st.error(f"找不到 '{person}' 的券商 '{broker}' 配置。")
                    return pd.DataFrame()
                sheet_id = broker_config['id']
                range_name = broker_config['range']
            else:
                sheet_id = config['id']
                range_name = config.get(f'{data_type}_range')
            
            if not range_name:
                return pd.DataFrame()

            result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                st.warning(f"'{person}' 的 '{range_name}' 工作表數據為空或格式不正確。")
                return pd.DataFrame()
            
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # 數據完整性檢查與格式轉換
            if person == 'ed_overseas':
                numeric_cols = [col for col in df.columns if any(k in col for k in ['價', '成本', '市值', '損益', '股數', '率'])]
            elif data_type == 'holdings':
                numeric_cols = ['總投入成本', '目前總市值', '未實現損益', '報酬率', '目前股價', '總持有股數']
                if not all(col in df.columns for col in numeric_cols):
                    st.warning(f"'{person}' 的持股數據缺少必要的欄位。")
            elif data_type == 'dca':
                numeric_cols = ['每月投入金額', '扣款日']
                if not all(col in df.columns for col in numeric_cols):
                    st.warning(f"'{person}' 的定期定額數據缺少必要的欄位。")
            elif data_type == 'trend':
                numeric_cols = ['總市值']
                if '日期' not in df.columns or '總市值' not in df.columns:
                    st.warning(f"'{person}' 的趨勢數據缺少必要的欄位。")
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].apply(DataLoader.parse_number)
            
            return df
            
        except Exception as e:
            st.error(f"載入 {person} {broker or data_type} 數據失敗: {e}")
            return pd.DataFrame()

    @staticmethod
    def append_to_sheet(spreadsheet_id, range_name, values):
        """將一列資料附加到指定的 Google Sheet 中，帶有重試機制"""
        service = DataLoader.get_google_sheets_service()
        if not service:
            return False
        
        for i in range(3): # 重試3次
            try:
                body = {'values': values}
                service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                return True
            except Exception as e:
                st.error(f"第 {i+1} 次寫入 Google Sheets 失敗: {e}")
                time.sleep(2)
        st.error("寫入 Google Sheets 失敗，請稍後再試。")
        return False

    @staticmethod
    def calculate_total_values(data_frames, usd_twd_rate):
        """計算各券商總市值並統一單位"""
        def get_value(df, key):
            if df.empty: return 0, 0
            if key == 'schwab':
                b_column = df.iloc[:, 1]
                for i in range(len(b_column) - 1, -1, -1):
                    value = b_column.iloc[i]
                    if pd.notna(value) and str(value).strip() != '':
                        parsed_value = DataLoader.parse_number(value)
                        if parsed_value > 0: return parsed_value, parsed_value * usd_twd_rate
                return 0, 0
            if key == 'cathay':
                f_column = df.iloc[:, 5]
                total_usd = sum(DataLoader.parse_number(v) for v in f_column if pd.notna(v) and str(v).strip() != '')
                return total_usd, total_usd * usd_twd_rate
            if key == 'fubon_uk':
                usd_col = next((col for col in df.columns if '市值' in col and 'USD' in col), None)
                if usd_col:
                    total_usd = df[usd_col].sum()
                    return total_usd, total_usd * usd_twd_rate
                return 0, 0
        
        schwab_usd, schwab_twd = get_value(data_frames['schwab'], 'schwab')
        cathay_usd, cathay_twd = get_value(data_frames['cathay'], 'cathay')
        fubon_usd, fubon_twd = get_value(data_frames['fubon_uk'], 'fubon_uk')
        
        return {
            'schwab_usd': schwab_usd, 'schwab_twd': schwab_twd,
            'cathay_usd': cathay_usd, 'cathay_twd': cathay_twd,
            'fubon_usd': fubon_usd, 'fubon_twd': fubon_twd,
            'total_usd': schwab_usd + cathay_usd + fubon_usd,
            'total_twd': schwab_twd + cathay_twd + fubon_twd
        }

    @staticmethod
    @st.cache_data(ttl=600, show_spinner="正在計算資產配置...")
    def get_asset_allocation_data():
        """計算資產配置數據，利用並行載入"""
        usd_twd_rate = DataLoader.get_usd_twd_rate()
        allocation_data = {cat: {'value_twd': 0.0, 'percentage': 0.0} for cat in AppConfig.TARGET_ALLOCATION.keys()}

        # 定義需要載入的數據任務
        tasks = {
            'rita': ('holdings', None),
            'ed': ('holdings', None),
            'schwab': ('ed_overseas', 'schwab'),
            'cathay': ('ed_overseas', 'cathay'),
            'fubon_uk': ('ed_overseas', 'fubon_uk'),
        }

        # 並行載入數據
        data_frames = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_key = {executor.submit(DataLoader.load_sheet_data, tasks[key][0], tasks[key][1], tasks[key][1]): key for key in tasks}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    data_frames[key] = future.result()
                except Exception as exc:
                    st.warning(f"數據載入失敗 ({key}): {exc}")
                    data_frames[key] = pd.DataFrame()
        
        # 1. Rita 台股投資
        rita_df = data_frames.get('rita', pd.DataFrame())
        if not rita_df.empty and '類別' in rita_df.columns and '目前總市值' in rita_df.columns:
            for _, row in rita_df.iterrows():
                category = str(row.get('類別', '')).strip()
                if category in allocation_data:
                    allocation_data[category]['value_twd'] += DataLoader.parse_number(row.get('目前總市值', 0))
        
        # 2. Ed 台股投資
        ed_df = data_frames.get('ed', pd.DataFrame())
        if not ed_df.empty and '類別' in ed_df.columns and '目前總市值' in ed_df.columns:
            for _, row in ed_df.iterrows():
                category = str(row.get('類別', '')).strip()
                if category in allocation_data:
                    allocation_data[category]['value_twd'] += DataLoader.parse_number(row.get('目前總市值', 0))
        
        # 3. Ed 海外投資 - 嘉信證券
        schwab_df = data_frames.get('schwab', pd.DataFrame())
        schwab_total_usd, _ = DataLoader.calculate_total_values({'schwab': schwab_df}, usd_twd_rate)
        if schwab_total_usd > 0:
            allocation_data['美股個股']['value_twd'] += schwab_total_usd * usd_twd_rate
        
        # 4. Ed 海外投資 - 國泰證券
        cathay_df = data_frames.get('cathay', pd.DataFrame())
        if not cathay_df.empty and len(cathay_df.columns) >= 8:
            for _, row in cathay_df.iterrows():
                category = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ''
                if category in allocation_data:
                    value_usd = DataLoader.parse_number(row.iloc[5])
                    if value_usd > 0:
                        allocation_data[category]['value_twd'] += value_usd * usd_twd_rate
        
        # 5. Ed 海外投資 - 富邦英股
        fubon_df = data_frames.get('fubon_uk', pd.DataFrame())
        if not fubon_df.empty and len(fubon_df.columns) >= 13:
            usd_col_idx = next((i for i, col in enumerate(fubon_df.columns) if '市值' in col and 'USD' in col), None)
            if usd_col_idx is not None:
                for _, row in fubon_df.iterrows():
                    category = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ''
                    if category in allocation_data:
                        value_usd = DataLoader.parse_number(row.iloc[usd_col_idx])
                        if value_usd > 0:
                            allocation_data[category]['value_twd'] += value_usd * usd_twd_rate

        # 計算總資產和百分比
        total_value = sum(data['value_twd'] for data in allocation_data.values())
        if total_value > 0:
            for category in allocation_data:
                allocation_data[category]['percentage'] = (allocation_data[category]['value_twd'] / total_value) * 100
        
        return allocation_data, total_value, usd_twd_rate


# ==============================================================================
# 3. UI 渲染模組 (UI Components Module)
# ==============================================================================
class UIComponents:
    """負責所有 UI 元件的渲染"""

    @staticmethod
    def render_css():
        """渲染自定義CSS樣式"""
        st.markdown(AppConfig.STYLE_CSS, unsafe_allow_html=True)

    @staticmethod
    def render_hero_section():
        """渲染頂部英雄區塊"""
        st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_user_selection():
        """渲染使用者選擇按鈕"""
        st.markdown('<div class="user-selection-container"></div>', unsafe_allow_html=True)
        cols = st.columns(len(AppConfig.USER_OPTIONS))
        
        if 'selected_person' not in st.session_state:
            st.session_state.selected_person = 'jason'
        
        for i, option in enumerate(AppConfig.USER_OPTIONS):
            with cols[i]:
                if st.button(f"{option['icon']}\n{option['label']}\n{option['desc']}", key=f"btn_{option['key']}", use_container_width=True):
                    st.session_state.selected_person = option['key']
        return st.session_state.selected_person

    @staticmethod
    def format_currency(amount, currency='TWD', show_prefix=True):
        """格式化貨幣"""
        if currency == 'USD':
            return f"${amount:,.2f}"
        else:
            if show_prefix: return f"NT${amount:,.0f}"
            else: return f"{amount:,.0f}"

    @staticmethod
    def format_percentage(value):
        """格式化百分比"""
        return f"{'+' if value > 0 else ''}{value:.2f}%"

    @staticmethod
    def render_summary_cards(holdings_df, dca_df=None):
        """渲染台股投資摘要卡片"""
        if holdings_df.empty: return
        try:
            total_cost = holdings_df['總投入成本'].sum()
            total_value = holdings_df['目前總市值'].sum()
            total_pl = holdings_df['未實現損益'].sum()
            total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">總投入成本</div><div class="metric-value">{UIComponents.format_currency(total_cost)}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-label">目前市值</div><div class="metric-value">{UIComponents.format_currency(total_value)}</div></div>', unsafe_allow_html=True)
            with col3:
                profit_class = 'profit' if total_pl >= 0 else 'loss'
                st.markdown(f'<div class="metric-card"><div class="metric-label">未實現損益</div><div class="metric-value {profit_class}">{UIComponents.format_currency(total_pl)}</div><div class="metric-change {profit_class}">{UIComponents.format_percentage(total_return)}</div></div>', unsafe_allow_html=True)
            with col4:
                UIComponents.render_dca_card(dca_df)
        except Exception as e:
            st.error(f"台股投資摘要卡片渲染錯誤: {e}")

    @staticmethod
    def render_dca_card(dca_df):
        """渲染定期定額卡片"""
        st.markdown('<div class="dca-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>', unsafe_allow_html=True)
        if dca_df is not None and not dca_df.empty:
            required_cols = ['股票代號', '股票名稱', '每月投入金額', '扣款日']
            if all(col in dca_df.columns for col in required_cols):
                for _, row in dca_df.iterrows():
                    if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                        st.markdown(f'<div class="dca-item"><strong>{row["股票代號"]} {row["股票名稱"]}</strong><br><small>每月{UIComponents.format_currency(row["每月投入金額"])} | {int(row["扣款日"])}號扣款</small></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="opacity: 0.8;">資料格式錯誤</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="opacity: 0.8;">暫無設定資料</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_ed_overseas_summary(total_values):
        """渲染ED海外投資綜合摘要卡片"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="schwab-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇺🇸 嘉信證券</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{UIComponents.format_currency(total_values["schwab_usd"], "USD")}</div><div style="opacity: 0.8;">美股個股總市值</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="cathay-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇹🇼 國泰證券</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{UIComponents.format_currency(total_values["cathay_usd"], "USD")}</div><div style="opacity: 0.8;">美股ETF總市值</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="fubon-card"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇬🇧 富邦英股</div><div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">{UIComponents.format_currency(total_values["fubon_usd"], "USD")}</div><div style="opacity: 0.8;">英股總市值</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card" style="border: none; background: #e8f5e9;"><div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #388e3c; opacity: 0.9;">總資產 (USD)</div><div style="font-size: 2.5rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem;">{UIComponents.format_currency(total_values["total_usd"], "USD")}</div><div style="opacity: 0.8;">三平台合計</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_asset_allocation_summary(allocation_data, total_value, usd_twd_rate):
        """渲染資產配置摘要"""
        st.subheader("🎯 目標 vs 實際配置比較")
        
        categories = list(AppConfig.TARGET_ALLOCATION.keys())
        target_percentages = [AppConfig.TARGET_ALLOCATION[cat] for cat in categories]
        actual_percentages = [allocation_data[cat]['percentage'] for cat in categories]
        actual_values = [allocation_data[cat]['value_twd'] for cat in categories]
        differences = [actual - target for actual, target in zip(actual_percentages, target_percentages)]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">總資產</div><div class="metric-value">{UIComponents.format_currency(total_value)}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">USD/TWD 匯率</div><div class="metric-value">{usd_twd_rate:.2f}</div></div>', unsafe_allow_html=True)
        
        comparison_df = pd.DataFrame({
            '資產類別': categories,
            '目標配置(%)': target_percentages,
            '實際配置(%)': [f"{x:.1f}" for x in actual_percentages],
            '實際金額(台幣)': [UIComponents.format_currency(x, show_prefix=False) for x in actual_values],
            '差距(%)': [f"{'+' if x > 0 else ''}{x:.1f}" for x in differences]
        })
        
        st.markdown("### 📊 配置詳細比較")
        st.dataframe(comparison_df.style.format({'目標配置(%)': "{:.0f}%"}).applymap(lambda x: 'color: green' if isinstance(x, str) and x.startswith('+') else ('color: red' if isinstance(x, str) and x.startswith('-') else ''), subset=['差距(%)']), use_container_width=True)
        return categories, target_percentages, actual_percentages, differences

    @staticmethod
    def render_allocation_charts(categories, target_percentages, actual_percentages, differences):
        """渲染資產配置圖表"""
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

    @staticmethod
    def render_holdings_table(holdings_df):
        """渲染台股持股表格"""
        if holdings_df.empty:
            st.info("查無持股數據。")
            return
        st.dataframe(
            holdings_df.style.format({
                '目前股價': "{:.2f}", '總持有股數': "{:,.0f}", '總投入成本': "NT${:,.0f}",
                '目前總市值': "NT${:,.0f}", '未實現損益': "NT${:,.0f}", '報酬率': "{:,.2f}%"
            }),
            use_container_width=True
        )

    @staticmethod
    def render_overseas_holdings_table(df, broker_name):
        """渲染海外持股表格"""
        if df.empty:
            st.info(f"查無 {broker_name} 持股數據。")
            return
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_portfolio_chart(holdings_df):
        """渲染台股資產配置圖表"""
        if holdings_df.empty: return
        portfolio_df = holdings_df[['股票名稱', '目前總市值']].copy()
        portfolio_df = portfolio_df[portfolio_df['目前總市值'] > 0]
        fig = px.pie(
            portfolio_df, values='目前總市值', names='股票名稱', 
            title='資產配置 (按市值)', hole=0.4, color_discrete_sequence=px.colors.sequential.Agsunset
        )
        fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_overseas_portfolio_chart(df, broker_name):
        """渲染海外資產配置圖表"""
        if df.empty: return
        try:
            value_col = next((col for col in df.columns if '市值' in col and ('USD' in col or 'NTD' not in col)), None)
            name_col = next((col for col in df.columns if '名稱' in col), None)
            if not value_col or not name_col:
                st.warning(f"找不到{broker_name}的市值或名稱欄位，無法繪製圖表。"); return
            portfolio_df = df[[name_col, value_col]].copy()
            portfolio_df = portfolio_df[portfolio_df[value_col] > 0]
            fig = px.pie(
                portfolio_df, values=value_col, names=name_col, 
                title=f'{broker_name} 資產配置 (按市值)', hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"{broker_name}圖表繪製失敗: {e}")

    @staticmethod
    def render_trend_chart(trend_df):
        """渲染資產趨勢圖"""
        if trend_df.empty:
            st.info("查無資產趨勢數據。"); return
        try:
            trend_df = trend_df.copy()
            trend_df['日期'] = pd.to_datetime(trend_df['日期'])
            trend_df['總市值'] = trend_df['總市值'].apply(DataLoader.parse_number)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_df['日期'], y=trend_df['總市值'], mode='lines+markers', name='總市值',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8, color='#3498db', line=dict(width=1, color='DarkSlateGrey'))
            ))
            fig.update_layout(title='資產趨勢', xaxis_title='日期', yaxis_title='總市值 (NT$)', hovermode='x unified', template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"資產趨勢圖繪製失敗: {e}"); st.write("數據預覽:", trend_df)

# ==============================================================================
# 4. 主程式應用邏輯 (App Logic)
# ==============================================================================
def render_taiwan_portfolio_page(person):
    """渲染個人台股投資總覽頁面"""
    st.header(f"{person.capitalize()} 台股投資總覽")
    
    # 預載入數據
    with st.spinner("正在載入台股投資數據..."):
        holdings_df = DataLoader.load_sheet_data(person, 'holdings')
        dca_df = DataLoader.load_sheet_data(person, 'dca')
        trend_df = DataLoader.load_sheet_data(person, 'trend')

    if not holdings_df.empty:
        UIComponents.render_summary_cards(holdings_df, dca_df)
        
        tab1, tab2, tab3 = st.tabs(["📈 持股明細", "🥧 資產配置", "📊 資產趨勢"])
        with tab1:
            st.subheader("持股明細")
            UIComponents.render_holdings_table(holdings_df)
        with tab2:
            st.subheader("資產配置")
            UIComponents.render_portfolio_chart(holdings_df)
        with tab3:
            st.subheader("資產趨勢")
            UIComponents.render_trend_chart(trend_df)
    else:
        st.warning(f"無法載入 {person} 的投資數據，或數據為空。")

def render_ed_overseas_page():
    """渲染Ed海外投資總覽頁面"""
    st.header("Ed 海外投資總覽")
    
    # 並行載入海外數據
    with st.spinner("正在載入海外投資數據..."):
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                'schwab': executor.submit(DataLoader.load_sheet_data, 'ed_overseas', None, 'schwab'),
                'cathay': executor.submit(DataLoader.load_sheet_data, 'ed_overseas', None, 'cathay'),
                'fubon_uk': executor.submit(DataLoader.load_sheet_data, 'ed_overseas', None, 'fubon_uk')
            }
            data_frames = {key: future.result() for key, future in futures.items()}

    usd_twd_rate = DataLoader.get_usd_twd_rate()
    total_values = DataLoader.calculate_total_values(data_frames, usd_twd_rate)
    
    UIComponents.render_ed_overseas_summary(total_values)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 嘉信證券", "🇹🇼 國泰證券", "🇬🇧 富邦英股", "📊 綜合分析"])
    
    with tab1:
        st.subheader("嘉信證券 - 美股個股")
        with st.form("schwab_append_form", clear_on_submit=True):
            st.write("##### ✏️ 新增一筆市值紀錄")
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1: record_date = st.date_input("紀錄日期", value=datetime.now())
            with c2: market_value = st.number_input("總市值 (USD)", min_value=0.0, format="%.2f")
            with c3:
                st.write("")
                st.write("")
                submitted = st.form_submit_button("新增至 Google Sheet")
        
        if submitted:
            sheet_id = AppConfig.SHEET_CONFIGS['ed_overseas']['schwab']['id']
            success = DataLoader.append_to_sheet(sheet_id, 'schwab', [[record_date.strftime('%Y/%m/%d'), market_value]])
            if success:
                st.success("紀錄已成功新增！正在重新整理數據...")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("新增紀錄失敗，請檢查後台日誌或 API 權限。")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            UIComponents.render_overseas_portfolio_chart(data_frames['schwab'], "嘉信證券")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            UIComponents.render_overseas_holdings_table(data_frames['schwab'], "嘉信證券")

    with tab2:
        st.subheader("國泰證券 - 美股ETF")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            UIComponents.render_overseas_portfolio_chart(data_frames['cathay'], "國泰證券")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            UIComponents.render_overseas_holdings_table(data_frames['cathay'], "國泰證券")
    
    with tab3:
        st.subheader("富邦證券 - 英股投資")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            UIComponents.render_overseas_portfolio_chart(data_frames['fubon_uk'], "富邦英股")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            UIComponents.render_overseas_holdings_table(data_frames['fubon_uk'], "富邦英股")
    
    with tab4:
        st.subheader("綜合投資分析")
        platforms = ['嘉信證券', '國泰證券', '富邦英股']
        values = [total_values['schwab_usd'], total_values['cathay_usd'], total_values['fubon_usd']]
        
        fig = px.bar(x=platforms, y=values, title='各平台投資總值比較 (USD)', color=platforms, color_discrete_sequence=['#1f4e79', '#8b0000', '#2d3436'])
        fig.update_layout(showlegend=False, yaxis_title='總市值 (USD)')
        st.plotly_chart(fig, use_container_width=True)

def render_asset_allocation_page():
    """渲染資產配置分析頁面"""
    st.header("📊 整體資產配置分析")
    
    allocation_data, total_value, usd_twd_rate = DataLoader.get_asset_allocation_data()
    
    if total_value > 0:
        categories, target_percentages, actual_percentages, differences = UIComponents.render_asset_allocation_summary(
            allocation_data, total_value, usd_twd_rate
        )
        
        st.markdown("---")
        UIComponents.render_allocation_charts(categories, target_percentages, actual_percentages, differences)
        
        st.markdown("### 💡 配置建議")
        suggestions = [f"• **{cat}** 目前超配 {diff:.1f}%，建議減少投入" if diff > 2 else f"• **{cat}** 目前低配 {abs(diff):.1f}%，建議增加投入" for cat, diff in zip(categories, differences) if abs(diff) > 2]
        
        if suggestions:
            for suggestion in suggestions:
                st.markdown(suggestion)
        else:
            st.success("🎉 目前配置與目標相當接近，維持現狀即可！")
    else:
        st.warning("無法取得資產配置數據，請檢查數據來源。")

def main():
    """主應用程式邏輯入口"""
    UIComponents.render_css()
    UIComponents.render_hero_section()
    
    person = UIComponents.render_user_selection()
    
    if st.button('重新載入數據', key='refresh_button'):
        st.cache_data.clear()
        st.rerun()

    if person == 'asset_allocation':
        render_asset_allocation_page()
    elif person == 'ed_overseas':
        render_ed_overseas_page()
    else:
        render_taiwan_portfolio_page(person)

if __name__ == "__main__":
    main()
