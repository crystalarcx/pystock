# settlement_refactored.py - 重構後的投資儀表板
"""
投資儀表板 - 重構版本
將原本的單體函數拆分為清晰的類別結構，提升可維護性和可擴展性
"""

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


# ========== 配置管理類 ==========
class Config:
    """配置管理類，集中管理所有配置"""
    
    # 應用程式配置
    APP_CONFIG = {
        'page_title': '投資總覽',
        'page_icon': '📈',
        'layout': 'wide',
        'initial_sidebar_state': 'collapsed'
    }
    
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
    
    # 使用者選項
    USER_OPTIONS = [
        {'key': 'jason', 'icon': '👨‍💼', 'label': 'Jason', 'desc': '台股投資'},
        {'key': 'rita', 'icon': '👩‍💼', 'label': 'Rita', 'desc': '台股投資'},
        {'key': 'ed', 'icon': '👨‍💻', 'label': 'Ed', 'desc': '台股投資'},
        {'key': 'ed_overseas', 'icon': '🌍', 'label': 'Ed', 'desc': '海外總覽'},
        {'key': 'asset_allocation', 'icon': '📊', 'label': '資產配置', 'desc': '整體配置'}
    ]


# ========== 工具函數類 ==========
class Utils:
    """工具函數集合"""
    
    @staticmethod
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
    
    @staticmethod
    def format_currency(amount, currency='TWD', show_prefix=True):
        """格式化貨幣"""
        if currency == 'USD':
            return f"${amount:,.2f}"
        else:
            if show_prefix:
                return f"NT${amount:,.0f}"
            else:
                return f"{amount:,.0f}"
    
    @staticmethod
    def format_percentage(value):
        """格式化百分比"""
        return f"{'+' if value > 0 else ''}{value:.2f}%"


# ========== 數據服務類 ==========
class DataService:
    """數據服務類，處理所有數據相關操作"""
    
    def __init__(self):
        self._service = None
    
    @st.cache_resource
    def get_google_sheets_service(_self):
        """獲得Google Sheets服務實例"""
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
    
    @st.cache_data(ttl=3600)
    def get_usd_twd_rate(_self):
        """獲得USDTWD 匯率"""
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
    
    @st.cache_data(ttl=600)
    def load_sheet_data(_self, person, data_type, broker=None):
        """從Google Sheets載入數據"""
        service = _self.get_google_sheets_service()
        if not service:
            return pd.DataFrame()
        
        try:
            if person == 'ed_overseas':
                config = Config.SHEET_CONFIGS[person][broker]
                sheet_id = config['id']
                range_name = config['range']
            else:
                config = Config.SHEET_CONFIGS[person]
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
            
            # 數值欄位處理
            numeric_columns = _self._get_numeric_columns(person, data_type)
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].apply(Utils.parse_number)
            
            return df
            
        except Exception as e:
            st.error(f"載入{person} {broker or data_type}數據失敗: {e}")
            return pd.DataFrame()
    
    def _get_numeric_columns(self, person, data_type):
        """獲取需要轉換為數值的欄位"""
        if person == 'ed_overseas':
            numeric_columns = []
            # 根據實際情況動態判斷
            return numeric_columns
        elif data_type == 'holdings':
            return [
                '總投入成本', '總持有股數', '目前股價', 
                '目前總市值', '未實現獲益', '報酬率'
            ]
        elif data_type == 'dca':
            return ['每月投入金額', '扣款日', '券商折扣']
        elif data_type == 'trend':
            return ['總市值']
        else:
            return []
    
    def append_to_sheet(self, spreadsheet_id, range_name, values):
        """將一列資料附加到指定的 Google Sheet 中"""
        try:
            service = self.get_google_sheets_service()
            if not service:
                st.error("無法連接至 Google Sheets 服務。")
                return False

            body = {'values': values}
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


# ========== 計算服務類 ==========
class CalculationService:
    """計算服務類，處理各種金融計算"""
    
    def __init__(self, data_service):
        self.data_service = data_service
    
    def calculate_portfolio_summary(self, holdings_df):
        """計算投資組合摘要"""
        try:
            total_cost = holdings_df['總投入成本'].sum()
            total_value = holdings_df['目前總市值'].sum()
            total_pl = holdings_df['未實現獲益'].sum()
            total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
            
            return {
                'total_cost': total_cost,
                'total_value': total_value,
                'total_pl': total_pl,
                'total_return': total_return
            }
        except Exception as e:
            st.error(f"計算投資組合摘要失敗: {e}")
            return {}
    
    def get_schwab_total_value(self, schwab_df):
        """從schwab工作表的B欄獲得最下方的總市值數據"""
        try:
            if schwab_df.empty or len(schwab_df.columns) < 2:
                return 0.0
            
            b_column = schwab_df.iloc[:, 1]
            
            for i in range(len(b_column) - 1, -1, -1):
                value = b_column.iloc[i]
                if pd.notna(value) and str(value).strip() != '':
                    parsed_value = Utils.parse_number(value)
                    if parsed_value > 0:
                        return parsed_value
            
            return 0.0
        except Exception as e:
            st.error(f"解析嘉信證券總市值失敗: {e}")
            return 0.0
    
    def get_cathay_total_value(self, cathay_df):
        """從總覽與獲益工作表的F欄計算總市值"""
        try:
            if cathay_df.empty or len(cathay_df.columns) < 6:
                return 0.0
            
            f_column = cathay_df.iloc[:, 5]
            
            total = 0.0
            for value in f_column:
                if pd.notna(value) and str(value).strip() != '':
                    parsed_value = Utils.parse_number(value)
                    if parsed_value > 0:
                        total += parsed_value
            
            return total
        except Exception as e:
            st.error(f"計算國泰證券總市值失敗: {e}")
            return 0.0
    
    def get_fubon_uk_total_value(self, fubon_df):
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
    
    def get_asset_allocation_data(self):
        """計算資產配置數據"""
        try:
            usd_twd_rate = self.data_service.get_usd_twd_rate()
            allocation_data = {category: {'value_twd': 0.0, 'percentage': 0.0} 
                             for category in Config.TARGET_ALLOCATION.keys()}
            
            # 1. Rita 台股投資
            rita_df = self.data_service.load_sheet_data('rita', 'holdings')
            self._process_domestic_allocation(rita_df, allocation_data)
            
            # 2. Ed 台股投資
            ed_df = self.data_service.load_sheet_data('ed', 'holdings')
            self._process_domestic_allocation(ed_df, allocation_data)
            
            # 3-5. 海外投資處理
            self._process_overseas_allocation(allocation_data, usd_twd_rate)
            
            # 計算總資產和百分比
            total_value = sum([data['value_twd'] for data in allocation_data.values()])
            
            if total_value > 0:
                for category in allocation_data:
                    allocation_data[category]['percentage'] = (
                        allocation_data[category]['value_twd'] / total_value
                    ) * 100
            
            return allocation_data, total_value, usd_twd_rate
            
        except Exception as e:
            st.error(f"計算資產配置失敗: {e}")
            return {}, 0.0, 31.0
    
    def _process_domestic_allocation(self, df, allocation_data):
        """處理台股投資配置"""
        if not df.empty and '類別' in df.columns and '目前總市值' in df.columns:
            for _, row in df.iterrows():
                category = row.get('類別', '').strip()
                if category in allocation_data:
                    value_twd = Utils.parse_number(row.get('目前總市值', 0))
                    allocation_data[category]['value_twd'] += value_twd
    
    def _process_overseas_allocation(self, allocation_data, usd_twd_rate):
        """處理海外投資配置"""
        # 嘉信證券 - 美股個股
        schwab_df = self.data_service.load_sheet_data('ed_overseas', None, 'schwab')
        schwab_total_usd = self.get_schwab_total_value(schwab_df)
        if schwab_total_usd > 0:
            allocation_data['美股個股']['value_twd'] += schwab_total_usd * usd_twd_rate
        
        # 國泰證券 - 使用類別欄位進行分類
        cathay_df = self.data_service.load_sheet_data('ed_overseas', None, 'cathay')
        if not cathay_df.empty and len(cathay_df.columns) >= 8:
            self._process_cathay_allocation(cathay_df, allocation_data, usd_twd_rate)
        
        # 富邦英股
        fubon_df = self.data_service.load_sheet_data('ed_overseas', None, 'fubon_uk')
        if not fubon_df.empty and len(fubon_df.columns) >= 13:
            self._process_fubon_allocation(fubon_df, allocation_data, usd_twd_rate)
    
    def _process_cathay_allocation(self, cathay_df, allocation_data, usd_twd_rate):
        """處理國泰證券配置"""
        category_col_idx = 7
        value_col_idx = 5
        
        for _, row in cathay_df.iterrows():
            if len(row) > max(category_col_idx, value_col_idx):
                category = str(row.iloc[category_col_idx]).strip() if pd.notna(row.iloc[category_col_idx]) else ''
                if category in allocation_data:
                    value_usd = Utils.parse_number(row.iloc[value_col_idx])
                    if value_usd > 0:
                        allocation_data[category]['value_twd'] += value_usd * usd_twd_rate
    
    def _process_fubon_allocation(self, fubon_df, allocation_data, usd_twd_rate):
        """處理富邦英股配置"""
        category_col_idx = 12
        
        value_usd_col_idx = None
        for i, col in enumerate(fubon_df.columns):
            if '市值' in col and 'USD' in col:
                value_usd_col_idx = i
                break
        
        if value_usd_col_idx is not None:
            for _, row in fubon_df.iterrows():
                if len(row) > max(category_col_idx, value_usd_col_idx):
                    category = str(row.iloc[category_col_idx]).strip() if pd.notna(row.iloc[category_col_idx]) else ''
                    if category in allocation_data:
                        value_usd = Utils.parse_number(row.iloc[value_usd_col_idx])
                        if value_usd > 0:
                            allocation_data[category]['value_twd'] += value_usd * usd_twd_rate


# ========== UI組件類 ==========
class UIComponents:
    """UI組件管理類"""
    
    def render_app_config(self):
        """設定頁面配置"""
        st.set_page_config(
            page_title=Config.APP_CONFIG['page_title'],
            page_icon=Config.APP_CONFIG['page_icon'],
            layout=Config.APP_CONFIG['layout'],
            initial_sidebar_state=Config.APP_CONFIG['initial_sidebar_state']
        )
    
    def render_css_styles(self):
        """渲染CSS樣式"""
        css_styles = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            * {
                font-family: 'Inter', sans-serif;
            }
            
            .main > div {
                padding-top: 1rem;
            }
            
            .css-1d391kg {
                display: none;
            }
            
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
            
            .dca-item {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
            }
            
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
            
            .chart-container {
                background: white;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
                margin-bottom: 2rem;
                border: 1px solid rgba(0,0,0,0.05);
            }
            
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
        </style>
        """
        st.markdown(css_styles, unsafe_allow_html=True)
    
    def render_hero_section(self):
        """渲染主標題區域"""
        st.markdown('''
        <div class="hero-section">
            <h1 class="hero-title">📈 投資儀表板</h1>
            <p class="hero-subtitle">快速掌握個人資產概況與趨勢</p>
        </div>
        ''', unsafe_allow_html=True)
    
    def render_user_selection(self):
        """渲染使用者選擇按鈕"""
        st.markdown('<div class="user-selection-container"></div>', unsafe_allow_html=True)
        
        cols = st.columns(len(Config.USER_OPTIONS))
        
        if 'selected_person' not in st.session_state:
            st.session_state.selected_person = 'jason'
        
        for i, option in enumerate(Config.USER_OPTIONS):
            with cols[i]:
                if st.button(
                    f"{option['icon']}\n{option['label']}\n{option['desc']}", 
                    key=f"btn_{option['key']}",
                    use_container_width=True
                ):
                    st.session_state.selected_person = option['key']
        
        return st.session_state.selected_person
    
    def render_refresh_button(self):
        """渲染更新數據按鈕"""
        if st.button('更新數據', key='refresh_button'):
            st.cache_data.clear()
            st.rerun()
    
    def render_summary_cards(self, summary_data, dca_df=None):
        """渲染摘要卡片"""
        if not summary_data:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">總投入成本</div>'
                f'<div class="metric-value">{Utils.format_currency(summary_data["total_cost"])}</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">目前市值</div>'
                f'<div class="metric-value">{Utils.format_currency(summary_data["total_value"])}</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col3:
            profit_class = 'profit' if summary_data['total_pl'] >= 0 else 'loss'
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">未實現獲益</div>'
                f'<div class="metric-value {profit_class}">{Utils.format_currency(summary_data["total_pl"])}</div>'
                f'<div class="metric-change {profit_class}">{Utils.format_percentage(summary_data["total_return"])}</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col4:
            self._render_dca_card(dca_df)
    
    def _render_dca_card(self, dca_df):
        """渲染定期定額卡片"""
        if dca_df is not None and not dca_df.empty:
            required_dca_columns = ['股票代號', '股票名稱', '每月投入金額', '扣款日']
            if all(col in dca_df.columns for col in required_dca_columns):
                with st.container():
                    st.markdown(
                        '<div class="dca-card">'
                        '<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>'
                        '</div>', 
                        unsafe_allow_html=True
                    )
                    for _, row in dca_df.iterrows():
                        if pd.notna(row['股票代號']) and pd.notna(row['股票名稱']):
                            st.markdown(
                                f'<div class="dca-item">'
                                f'<strong>{row["股票代號"]} {row["股票名稱"]}</strong><br>'
                                f'<small>每月{Utils.format_currency(row["每月投入金額"])} | '
                                f'{int(row["扣款日"])}號扣款</small>'
                                f'</div>', 
                                unsafe_allow_html=True
                            )
            else:
                st.markdown(
                    '<div class="dca-card">'
                    '<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>'
                    '<div style="opacity: 0.8;">資料格式錯誤</div>'
                    '</div>', 
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="dca-card">'
                '<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📅 定期定額設定</div>'
                '<div style="opacity: 0.8;">暫無設定資料</div>'
                '</div>', 
                unsafe_allow_html=True
            )
    
    def render_overseas_summary(self, schwab_total_usd, cathay_total_usd, fubon_total_usd, fubon_total_ntd):
        """渲染ED海外投資綜合摘要卡片"""
        total_combined_usd = schwab_total_usd + cathay_total_usd + fubon_total_usd
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f'<div class="schwab-card">'
                f'<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇺🇸 嘉信證券</div>'
                f'<div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">'
                f'{Utils.format_currency(schwab_total_usd, "USD")}</div>'
                f'<div style="opacity: 0.8;">美股個股總市值</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f'<div class="cathay-card">'
                f'<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇹🇼 國泰證券</div>'
                f'<div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">'
                f'{Utils.format_currency(cathay_total_usd, "USD")}</div>'
                f'<div style="opacity: 0.8;">美股ETF總市值</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f'<div class="fubon-card">'
                f'<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; opacity: 0.9;">🇬🇧 富邦英股</div>'
                f'<div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">'
                f'{Utils.format_currency(fubon_total_usd, "USD")}</div>'
                f'<div style="opacity: 0.8;">英股總市值</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f'<div class="metric-card" style="border: none; background: #e8f5e9;">'
                f'<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #388e3c; opacity: 0.9;">總資產 (USD)</div>'
                f'<div style="font-size: 2.5rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem;">'
                f'{Utils.format_currency(total_combined_usd, "USD")}</div>'
                f'<div style="opacity: 0.8;">三平台合計</div>'
                f'</div>', 
                unsafe_allow_html=True
            )


# ========== 表格渲染類 ==========
class TableRenderer:
    """表格渲染器"""
    
    def render_holdings_table(self, holdings_df, person):
        """渲染持股明細表格"""
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
                    '未實現獲益': "NT${:,.0f}",
                    '報酬率': "{:,.2f}%"
                }),
                use_container_width=True
            )
    
    def render_overseas_holdings_table(self, df, broker_name):
        """渲染海外持股表格"""
        if df.empty:
            st.info(f"查無{broker_name}持股數據。")
            return
        
        if broker_name == "富邦英股":
            display_df = df.rename(columns={
                '目前美價': '美價(USD)', '總持有股數': '股數',
                '總投入成本(USD)': '成本(USD)', '目前總市值(USD)': '市值(USD)',
                '未實現獲益(USD)': '獲益(USD)', '未實現報酬率': '報酬率%',
                '總未實現獲益%': '總報酬率%'
            })
            display_columns = [
                '股票代號', '股票名稱', '美價(USD)', '股數', 
                '成本(USD)', '市值(USD)', '獲益(USD)', '報酬率%'
            ]
            display_columns = [col for col in display_columns if col in display_df.columns]
            st.dataframe(
                display_df[display_columns].style.format({
                    '美價(USD)': "{:.2f}", '股數': "{:,.0f}",
                    '成本(USD)': "${:,.0f}", '市值(USD)': "${:,.0f}",
                    '獲益(USD)': "${:,.0f}", '報酬率%': "{:,.2f}%"
                }),
                use_container_width=True
            )
        else:
            st.dataframe(df, use_container_width=True)


# ========== 圖表渲染類 ==========
class ChartRenderer:
    """圖表渲染器"""
    
    def render_portfolio_chart(self, holdings_df, person):
        """渲染投資組合餅狀圖"""
        if holdings_df.empty: 
            return
            
        if person != 'ed_overseas':
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
    
    def render_overseas_portfolio_chart(self, df, broker_name):
        """渲染海外投資組合餅狀圖"""
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
                st.warning(f"找不到{broker_name}的市值或名稱欄位，無法繪製圖表。")
                return
                
            portfolio_df = df[[name_col, value_col]].copy()
            portfolio_df = portfolio_df[portfolio_df[value_col] > 0]
            
            fig = px.pie(
                portfolio_df, 
                values=value_col, 
                names=name_col, 
                title=f'{broker_name} 資產配置 (按市值)', 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_traces(textinfo='percent+label', pull=[0.1]*len(portfolio_df))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"{broker_name}圖表繪製失敗: {e}")
    
    def render_trend_chart(self, trend_df):
        """渲染資產趨勢圖"""
        if trend_df.empty:
            st.info("查無資產趨勢數據。")
            return
        try:
            trend_df = trend_df.copy()
            trend_df['日期'] = pd.to_datetime(trend_df['日期'])
            trend_df['總市值'] = trend_df['總市值'].apply(Utils.parse_number)
            
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
    
    def render_allocation_charts(self, categories, target_percentages, actual_percentages, differences):
        """渲染資產配置圖表"""
        col1, col2 = st.columns(2)
        
        with col1:
            # 目標 vs 實際配置比較圖
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name='目標配置',
                x=categories,
                y=target_percentages,
                marker_color='rgba(52, 152, 219, 0.7)'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name='實際配置',
                x=categories,
                y=actual_percentages,
                marker_color='rgba(231, 76, 60, 0.7)'
            ))
            
            fig_comparison.update_layout(
                title='目標 vs 實際配置比較',
                xaxis_title='資產類別',
                yaxis_title='配置比例(%)',
                barmode='group',
                template="plotly_white"
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with col2:
            # 配置差距圖
            colors = ['green' if x >= 0 else 'red' for x in differences]
            
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
                yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black')
            )
            
            st.plotly_chart(fig_diff, use_container_width=True)
        
        # 餅狀圖比較
        col3, col4 = st.columns(2)
        
        with col3:
            fig_target_pie = px.pie(
                values=target_percentages,
                names=categories,
                title='目標資產配置',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig_target_pie, use_container_width=True)
        
        with col4:
            fig_actual_pie = px.pie(
                values=actual_percentages,
                names=categories,
                title='實際資產配置',
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            st.plotly_chart(fig_actual_pie, use_container_width=True)


# ========== 主應用程式類 ==========
class InvestmentDashboard:
    """主應用程式類，統籌所有組件"""
    
    def __init__(self):
        self.ui_components = UIComponents()
        self.data_service = DataService()
        self.calculation_service = CalculationService(self.data_service)
        self.table_renderer = TableRenderer()
        self.chart_renderer = ChartRenderer()
    
    def initialize_app(self):
        """初始化應用程式"""
        self.ui_components.render_app_config()
        self.ui_components.render_css_styles()
    
    def run(self):
        """運行主應用程式"""
        self.initialize_app()
        
        # 渲染主標題和使用者選擇
        self.ui_components.render_hero_section()
        person = self.ui_components.render_user_selection()
        self.ui_components.render_refresh_button()
        
        # 根據選擇的人員渲染對應頁面
        if person == 'asset_allocation':
            self._render_asset_allocation_page()
        elif person == 'ed_overseas':
            self._render_ed_overseas_page()
        else:
            self._render_domestic_investment_page(person)
    
    def _render_asset_allocation_page(self):
        """渲染資產配置頁面"""
        st.header("📊 整體資產配置分析")
        
        with st.spinner('正在計算資產配置...'):
            allocation_data, total_value, usd_twd_rate = self.calculation_service.get_asset_allocation_data()
        
        if total_value > 0:
            categories, target_percentages, actual_percentages, differences = self._render_asset_allocation_summary(
                allocation_data, total_value, usd_twd_rate
            )
            
            st.markdown("---")
            self.chart_renderer.render_allocation_charts(categories, target_percentages, actual_percentages, differences)
            
            # 建議調整
            st.markdown("### 💡 配置建議")
            self._render_allocation_suggestions(categories, differences)
        else:
            st.warning("無法取得資產配置數據，請檢查數據來源。")
    
    def _render_asset_allocation_summary(self, allocation_data, total_value, usd_twd_rate):
        """渲染資產配置摘要"""
        st.subheader("🎯 目標 vs 實際配置比較")
        
        # 創建比較數據
        categories = list(Config.TARGET_ALLOCATION.keys())
        target_percentages = [Config.TARGET_ALLOCATION[cat] for cat in categories]
        actual_percentages = [allocation_data[cat]['percentage'] for cat in categories]
        actual_values = [allocation_data[cat]['value_twd'] for cat in categories]
        differences = [actual - target for actual, target in zip(actual_percentages, target_percentages)]
        
        # 顯示總資產和匯率
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">總資產</div><div class="metric-value">{Utils.format_currency(total_value)}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">USD/TWD 匯率</div><div class="metric-value">{usd_twd_rate:.2f}</div></div>', unsafe_allow_html=True)
        
        # 配置比較表格
        comparison_df = pd.DataFrame({
            '資產類別': categories,
            '目標配置(%)': target_percentages,
            '實際配置(%)': [f"{x:.1f}" for x in actual_percentages],
            '實際金額(台幣)': [Utils.format_currency(x, show_prefix=False) for x in actual_values],
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
    
    def _render_allocation_suggestions(self, categories, differences):
        """渲染配置建議"""
        suggestions = []
        for cat, diff in zip(categories, differences):
            if abs(diff) > 2:  # 如果差距超過2%
                if diff > 0:
                    suggestions.append(f"• **{cat}** 目前超配 {diff:.1f}%，建議減少投入")
                else:
                    suggestions.append(f"• **{cat}** 目前低配 {abs(diff):.1f}%，建議增加投入")
        
        if suggestions:
            for suggestion in suggestions:
                st.markdown(suggestion)
        else:
            st.success("🎉 目前配置與目標相當接近，維持現狀即可！")
    
    def _render_ed_overseas_page(self):
        """渲染Ed海外投資頁面"""
        st.header("Ed 海外投資總覽")
        
        # 載入各平台數據
        schwab_df = self.data_service.load_sheet_data('ed_overseas', None, 'schwab')
        cathay_df = self.data_service.load_sheet_data('ed_overseas', None, 'cathay')
        fubon_df = self.data_service.load_sheet_data('ed_overseas', None, 'fubon_uk')

        # 計算總市值
        schwab_total_usd = self.calculation_service.get_schwab_total_value(schwab_df)
        cathay_total_usd = self.calculation_service.get_cathay_total_value(cathay_df)
        fubon_total_usd, fubon_total_ntd = self.calculation_service.get_fubon_uk_total_value(fubon_df)
        
        # 渲染摘要卡片
        self.ui_components.render_overseas_summary(schwab_total_usd, cathay_total_usd, fubon_total_usd, fubon_total_ntd)
        
        # 渲染各平台詳細資訊
        tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 嘉信證券", "🇹🇼 國泰證券", "🇬🇧 富邦英股", "📊 綜合分析"])
        
        with tab1:
            self._render_schwab_tab(schwab_df)
        
        with tab2:
            self._render_cathay_tab(cathay_df)
        
        with tab3:
            self._render_fubon_tab(fubon_df)
        
        with tab4:
            self._render_overseas_combined_analysis(schwab_total_usd, cathay_total_usd, fubon_total_usd)
    
    def _render_schwab_tab(self, schwab_df):
        """渲染嘉信證券標籤頁"""
        st.subheader("嘉信證券 - 美股個股")
        
        # 新增寫入功能區塊
        with st.form("schwab_append_form", clear_on_submit=True):
            st.write("##### ✏️ 新增一筆市值紀錄")
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
            sheet_id = Config.SHEET_CONFIGS['ed_overseas']['schwab']['id']
            worksheet_name = 'schwab'
            
            date_str = record_date.strftime('%Y/%m/%d')
            values_to_append = [[date_str, market_value]]
            
            success = self.data_service.append_to_sheet(sheet_id, worksheet_name, values_to_append)
            
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
            self.chart_renderer.render_overseas_portfolio_chart(schwab_df, "嘉信證券")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            self.table_renderer.render_overseas_holdings_table(schwab_df, "嘉信證券")
    
    def _render_cathay_tab(self, cathay_df):
        """渲染國泰證券標籤頁"""
        st.subheader("國泰證券 - 美股ETF")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            self.chart_renderer.render_overseas_portfolio_chart(cathay_df, "國泰證券")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            self.table_renderer.render_overseas_holdings_table(cathay_df, "國泰證券")
    
    def _render_fubon_tab(self, fubon_df):
        """渲染富邦英股標籤頁"""
        st.subheader("富邦證券 - 英股投資")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            self.chart_renderer.render_overseas_portfolio_chart(fubon_df, "富邦英股")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            self.table_renderer.render_overseas_holdings_table(fubon_df, "富邦英股")
    
    def _render_overseas_combined_analysis(self, schwab_total_usd, cathay_total_usd, fubon_total_usd):
        """渲染海外投資綜合分析"""
        st.subheader("綜合投資分析")
        platforms = ['嘉信證券', '國泰證券', '富邦英股']
        values = [schwab_total_usd, cathay_total_usd, fubon_total_usd]
        
        fig = px.bar(
            x=platforms, 
            y=values, 
            title='各平台投資總值比較 (USD)',
            color=platforms, 
            color_discrete_sequence=['#1f4e79', '#8b0000', '#2d3436']
        )
        fig.update_layout(showlegend=False, yaxis_title='總市值 (USD)')
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_domestic_investment_page(self, person):
        """渲染台股投資頁面"""
        st.header(f"{person.capitalize()} 台股投資總覽")
        
        # 載入數據
        holdings_df = self.data_service.load_sheet_data(person, 'holdings')
        dca_df = self.data_service.load_sheet_data(person, 'dca')
        trend_df = self.data_service.load_sheet_data(person, 'trend')

        if not holdings_df.empty:
            # 計算摘要數據並渲染摘要卡片
            summary_data = self.calculation_service.calculate_portfolio_summary(holdings_df)
            self.ui_components.render_summary_cards(summary_data, dca_df)
            
            # 渲染詳細標籤頁
            tab1, tab2, tab3 = st.tabs(["📈 持股明細", "🥧 資產配置", "📊 資產趨勢"])
            
            with tab1:
                st.subheader("持股明細")
                self.table_renderer.render_holdings_table(holdings_df, person)
            
            with tab2:
                st.subheader("資產配置")
                self.chart_renderer.render_portfolio_chart(holdings_df, person)
            
            with tab3:
                st.subheader("資產趨勢")
                self.chart_renderer.render_trend_chart(trend_df)
        else:
            st.warning(f"無法載入 {person} 的投資數據，或數據為空。")


# ========== 主程式進入點 ==========
def main():
    """主程式進入點"""
    dashboard = InvestmentDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
