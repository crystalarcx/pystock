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
    'os': {
        'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
        'holdings_range': '總覽與損益!A:L'
    },
    'combined': {
        'id': '103Q3rZqZihu70jL3fHbVtU0hbFmzXb4n2708awhKiG0',
        'schwab_range': 'schwab!A:Z', # 擴大範圍確保能抓到所有資料
        'cathay_range': '總覽與損益!A:Z' # 擴大範圍確保能抓到所有資料
    }
}

@st.cache_resource
def get_google_sheets_service():
    """獲取Google Sheets服務實例"""
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

@st.cache_data(ttl=600) # 快取10分鐘，減少API呼叫
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
        elif data_type == 'schwab' or data_type == 'cathay':
            # 新增的嘉信和國泰數據處理
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['價', '成本', '市值', '損益', '股數', '率', '金額']):
                    numeric_columns.append(col)
        
        # 轉換數字欄位
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_number)
        
        return df
        
    except Exception as e:
        st.error(f"載入{person} {data_type}數據失敗: {e}")
        return pd.DataFrame()

def get_schwab_total_value():
    """獲取嘉信證券總市值 - Column B最下方的數據"""
    service = get_google_sheets_service()
    if not service:
        return 0
    
    try:
        sheet_id = SHEET_CONFIGS['combined']['id']
        
        # 先獲取整個B欄的數據
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='schwab!B:B'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return 0
        
        # 從後往前找最後一個有效數字
        for i in range(len(values) - 1, -1, -1):
            if values[i] and len(values[i]) > 0:
                try:
                    value = parse_number(values[i][0])
                    if value > 0: # 確保是正數
                        return value
                except:
                    continue
        
        return 0
        
    except Exception as e:
        st.error(f"獲取嘉信證券總市值失敗: {e}")
        return 0

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
    return f"{'%+' if value > 0 else ''}{value:.2f}%"

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

def render_cathay_table(cathay_df):
    """渲染國泰證券持股表格"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("國泰證券定期定額明細")
    
    if cathay_df.empty:
        st.warning("無國泰證券數據")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    try:
        # 顯示原始數據，讓用戶查看實際的欄位結構
        display_df = cathay_df.copy()
        
        # 格式化數值欄位 - C, E, F, G 欄位為美元計價，移除NT前綴
        usd_columns = ['C', 'E', 'F', 'G']  # 美元計價欄位
        
        for col in display_df.columns:
            if col in usd_columns:
                try:
                    # 美元欄位格式化，不加NT$前綴
                    display_df[col] = display_df[col].apply(
                        lambda x: f"${parse_number(x):,.2f}" if pd.notna(x) and str(x).strip() != '' else x
                    )
                except:
                    pass
            elif any(keyword in str(col) for keyword in ['價', '成本', '市值', '損益', '金額']):
                try:
                    # 其他可能的金額欄位保持原有格式
                    display_df[col] = display_df[col].apply(
                        lambda x: format_currency(parse_number(x), 'TWD') if pd.notna(x) and str(x).strip() != '' else x
                    )
                except:
                    pass
        
        # 設定顏色樣式
        def color_negative_red(val):
            # 修復語法錯誤
            if isinstance(val, str) and ('-' in val or 'NT$' in val):
                return 'color: #e74c3c; font-weight: bold'
            elif isinstance(val, str) and '+' in val and '%' in val:
                return 'color: #27ae60; font-weight: bold'
            return ''
        
        styled_df = display_df.style.applymap(color_negative_red)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"國泰證券表格渲染錯誤: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_charts(person, holdings_df):
    """渲染圖表"""
    if holdings_df.empty:
        st.warning("無數據可顯示圖表")
        return
    
    if person == 'os':
        # 海外投資圖表 - 動態處理欄位
        try:
            value_col = None
            pl_col = None
            
            for col in holdings_df.columns:
                if '市值' in col and 'USD' in col:
                    value_col = col
                elif '未實現' in col and 'USD' in col and '損益' in col:
                    pl_col = col
            
            if not value_col:
                st.warning("找不到合適的市值欄位")
                return
                
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("投資組合分佈 (USD)")
                fig_portfolio = px.pie(
                    values=holdings_df[value_col],
                    names=holdings_df['股票名稱'] if '股票名稱' in holdings_df.columns else holdings_df.iloc[:, 1],
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_portfolio.update_traces(textposition='inside', textinfo='percent+label')
                fig_portfolio.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_portfolio, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if pl_col:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader("損益分佈 (USD)")
                    holdings_df_filtered = holdings_df[holdings_df[pl_col] != 0]
                    if not holdings_df_filtered.empty:
                        fig_pl = px.bar(
                            holdings_df_filtered,
                            x=holdings_df_filtered['股票名稱'] if '股票名稱' in holdings_df_filtered.columns else holdings_df_filtered.iloc[:, 1],
                            y=pl_col,
                            color=pl_col,
                            color_continuous_scale=px.colors.diverging.RdYlGn,
                            labels={pl_col: "未實現損益 (USD)"},
                        )
                        fig_pl.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20), xaxis_title='', yaxis_title='未實現損益 (USD)')
                        st.plotly_chart(fig_pl, use_container_width=True)
                    else:
                        st.info("所有持股目前損益為零。")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"海外投資圖表渲染錯誤: {e}")
            with st.expander("查看可用欄位 (調試用)"):
                st.write("Available columns:", holdings_df.columns.tolist())
    
    else:
        # 台股投資圖表
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("投資組合分佈")
            fig_portfolio = px.pie(
                values=holdings_df['目前總市值'],
                names=holdings_df['股票名稱'],
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_portfolio.update_traces(textposition='inside', textinfo='percent+label')
            fig_portfolio.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_portfolio, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("損益分佈")
            # 篩選掉損益為0的項目
            pl_df = holdings_df[holdings_df['未實現損益'] != 0].copy()
            if not pl_df.empty:
                fig_pl = px.bar(
                    pl_df,
                    x='股票名稱',
                    y='未實現損益',
                    color='未實現損益',
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    labels={'未實現損益': "未實現損益 (NTD)"},
                )
                fig_pl.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20), xaxis_title='', yaxis_title='未實現損益 (NTD)')
                st.plotly_chart(fig_pl, use_container_width=True)
            else:
                st.info("所有持股目前損益為零。")
            st.markdown('</div>', unsafe_allow_html=True)

def render_trend_chart(trend_df):
    """渲染資產趨勢圖"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("資產總市值趨勢")
    
    if trend_df.empty:
        st.warning("無資產趨勢數據")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    try:
        trend_df = trend_df.dropna(subset=['日期', '總市值'])
        if trend_df.empty:
            st.warning("無資產趨勢數據可供繪製")
            st.markdown('</div>', unsafe_allow_html=True)
            return
            
        # 轉換日期格式
        trend_df['日期'] = pd.to_datetime(trend_df['日期'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['日期'], 
            y=trend_df['總市值'], 
            mode='lines+markers', 
            name='總市值',
            line=dict(color='#3498db', width=2),
            marker=dict(size=8, color='#2980b9', symbol='circle')
        ))
        
        fig.update_layout(
            title_text='資產總市值隨時間變化',
            xaxis_title='日期',
            yaxis_title='總市值 (NTD)',
            margin=dict(l=20, r=20, t=50, b=20),
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"資產趨勢圖渲染錯誤: {e}")
        st.write("請確認「資產趨勢」工作表格式是否正確，第一欄為日期，第二欄為總市值。")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_holdings_table(person, holdings_df):
    """渲染持股明細表格"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("持股明細")
    if holdings_df.empty:
        st.warning("無持股明細數據")
    else:
        try:
            display_df = holdings_df.copy()
            
            # 依據 '未實現損益' 欄位排序
            pl_col = '未實現損益' if '未實現損益' in display_df.columns else '未實現損益(USD)'
            if pl_col in display_df.columns:
                display_df = display_df.sort_values(by=pl_col, ascending=False).reset_index(drop=True)

            def color_pl(val):
                if isinstance(val, (int, float)):
                    color = '#e74c3c' if val < 0 else '#27ae60'
                    return f'color: {color}; font-weight: bold'
                return ''
            
            def color_rate(val):
                if isinstance(val, (int, float)):
                    color = '#e74c3c' if val < 0 else '#27ae60'
                    return f'color: {color}; font-weight: bold'
                return ''
            
            # 格式化欄位並套用顏色
            format_dict = {}
            styles_dict = {}

            if person == 'os':
                # 海外投資格式化
                if '總投入成本(USD)' in display_df.columns:
                    format_dict['總投入成本(USD)'] = lambda x: f"${x:,.2f}"
                if '目前總市值(USD)' in display_df.columns:
                    format_dict['目前總市值(USD)'] = lambda x: f"${x:,.2f}"
                if '未實現損益(USD)' in display_df.columns:
                    format_dict['未實現損益(USD)'] = lambda x: f"${x:,.2f}"
                    styles_dict['未實現損益(USD)'] = color_pl
                if '未實現報酬率' in display_df.columns:
                    format_dict['未實現報酬率'] = lambda x: f"{x:,.2f}%"
                    styles_dict['未實現報酬率'] = color_rate

            else:
                # 台股投資格式化
                if '總投入成本' in display_df.columns:
                    format_dict['總投入成本'] = lambda x: f"NT${x:,.0f}"
                if '目前總市值' in display_df.columns:
                    format_dict['目前總市值'] = lambda x: f"NT${x:,.0f}"
                if '未實現損益' in display_df.columns:
                    format_dict['未實現損益'] = lambda x: f"NT${x:,.0f}"
                    styles_dict['未實現損益'] = color_pl
                if '報酬率' in display_df.columns:
                    format_dict['報酬率'] = lambda x: f"{x:,.2f}%"
                    styles_dict['報酬率'] = color_rate
                if '目前股價' in display_df.columns:
                    format_dict['目前股價'] = lambda x: f"{x:,.2f}"
            
            styled_df = display_df.style.format(format_dict).apply(
                lambda s: s.map(styles_dict.get(s.name, lambda x: ''), na_action='ignore')
            )
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"持股明細表渲染錯誤: {e}")
            with st.expander("查看原始數據 (調試用)"):
                st.dataframe(holdings_df)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_combined_page():
    """渲染綜合投資頁面"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">綜合投資總覽</h1>
        <p class="hero-subtitle">美股與台股資產一站式檢視</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 載入數據
    schwab_total = get_schwab_total_value()
    cathay_df = load_sheet_data('combined', 'cathay')
    
    st.info("目前此頁面僅顯示嘉信證券與國泰證券的總市值，損益和詳細明細請至個別頁面查看。")
    
    # 渲染摘要卡片
    render_combined_summary_cards(schwab_total, cathay_df)

    # 渲染表格
    if not cathay_df.empty:
        render_cathay_table(cathay_df)
    
    st.markdown('<br>', unsafe_allow_html=True)
    
    if st.button("🔄 重新整理數據"):
        st.cache_data.clear()
        st.rerun()

def render_person_page(person):
    """渲染個人投資頁面"""
    person_name_map = {'jason': 'Jason', 'rita': 'Rita', 'ed': 'Ed', 'os': '海外投資'}
    
    st.markdown(f"""
    <div class="hero-section">
        <h1 class="hero-title">{person_name_map.get(person, '投資')}總覽</h1>
        <p class="hero-subtitle">即時追蹤您的投資組合與損益</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 載入數據
    holdings_df = load_sheet_data(person, 'holdings')
    dca_df = load_sheet_data(person, 'dca')
    trend_df = load_sheet_data(person, 'trend')

    # 渲染摘要卡片
    if not holdings_df.empty:
        render_summary_cards(person, holdings_df, dca_df)
    
    st.markdown("---")
    
    # 渲染標籤頁
    tab1, tab2, tab3 = st.tabs(["📊 持股概覽", "📈 資產趨勢", "📋 持股明細"])
    
    with tab1:
        if not holdings_df.empty:
            render_charts(person, holdings_df)
        else:
            st.warning("無數據可顯示圖表，請檢查Google Sheets設定。")

    with tab2:
        if not trend_df.empty:
            render_trend_chart(trend_df)
        else:
            st.warning("無資產趨勢數據，請檢查Google Sheets中的「資產趨勢」工作表。")
    
    with tab3:
        if not holdings_df.empty:
            render_holdings_table(person, holdings_df)
        else:
            st.warning("無持股明細數據。")
            
    st.markdown('<br>', unsafe_allow_html=True)
    
    if st.button("🔄 重新整理數據"):
        st.cache_data.clear()
        st.rerun()

# 主應用程式邏輯
if __name__ == '__main__':
    st.title("多帳戶投資儀表板")
    
    # 使用 Streamlit 的 selectbox 選擇投資者
    person = st.selectbox(
        "選擇投資者/帳戶:",
        ('jason', 'rita', 'ed', 'os', 'combined'),
        format_func=lambda x: {'jason': 'Jason', 'rita': 'Rita', 'ed': 'Ed', 'os': '海外投資', 'combined': '綜合投資'}[x]
    )
    
    st.markdown("---")
    
    if person == 'combined':
        render_combined_page()
    else:
        render_person_page(person)
