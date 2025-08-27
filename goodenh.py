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
    page_title="智慧投資總覽",
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
    'os': {
        'id': '1WlUslUTcXR-eVK-RdQAHv5Qqyg35xIyHqZgejYYvTIA',
        'holdings_range': '總覽與損益!A:L'
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

@st.cache_data(ttl=300)  # 快取5分鐘
def load_sheet_data(person, data_type):
    """從Google Sheets載入數據"""
    service = get_google_sheets_service()
    if not service:
        return pd.DataFrame()
    
    try:
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
        
        # 轉換數字欄位
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_number)
        
        return df
        
    except Exception as e:
        st.error(f"載入{person} {data_type}數據失敗: {e}")
        return pd.DataFrame()

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
                # 移除圓餅圖內的標籤
                fig_portfolio.update_traces(textposition='outside', textinfo='percent')
                fig_portfolio.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig_portfolio, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if pl_col:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader("投資損益分析")
                    # 創建顏色列表 - 正值藍色，負值紅色
                    colors = ['#3498db' if val >= 0 else '#e74c3c' for val in holdings_df[pl_col]]
                    
                    fig_pl = px.bar(
                        x=holdings_df['股票名稱'] if '股票名稱' in holdings_df.columns else holdings_df.iloc[:, 1],
                        y=holdings_df[pl_col],
                        color=holdings_df[pl_col],
                        color_discrete_map={val: color for val, color in zip(holdings_df[pl_col], colors)},
                        color_continuous_scale=None
                    )
                    # 手動設置顏色
                    fig_pl.update_traces(marker_color=colors)
                    fig_pl.update_layout(
                        height=400,
                        yaxis_title="損益 (USD)",
                        xaxis_title="股票",
                        showlegend=False
                    )
                    st.plotly_chart(fig_pl, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"海外投資圖表渲染錯誤: {e}")
    
    else:
        # 台股圖表
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("投資組合分佈")
            holdings_df['股票標籤'] = holdings_df['股票代號'] + ' ' + holdings_df['股票名稱']
            fig_portfolio = px.pie(
                values=holdings_df['目前總市值'],
                names=holdings_df['股票標籤'],
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            # 移除圓餅圖內的標籤
            fig_portfolio.update_traces(textposition='outside', textinfo='percent')
            fig_portfolio.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_portfolio, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("損益分析")
            # 創建顏色列表 - 正值藍色，負值紅色
            colors = ['#3498db' if val >= 0 else '#e74c3c' for val in holdings_df['未實現損益']]
            
            fig_pl = px.bar(
                x=holdings_df['股票標籤'],
                y=holdings_df['未實現損益'],
                color=holdings_df['未實現損益'],
                color_discrete_map={val: color for val, color in zip(holdings_df['未實現損益'], colors)},
                color_continuous_scale=None
            )
            # 手動設置顏色
            fig_pl.update_traces(marker_color=colors)
            fig_pl.update_layout(
                height=400,
                yaxis_title="損益 (NTD)",
                xaxis_title="股票",
                showlegend=False
            )
            st.plotly_chart(fig_pl, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def render_trend_chart(person, trend_df):
    """渲染資產趨勢圖表"""
    if trend_df.empty:
        return
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📈 資產趨勢變化")
    
    # 計算變化
    trend_df['變化金額'] = trend_df['總市值'].diff()
    trend_df['變化百分比'] = trend_df['總市值'].pct_change() * 100
    
    # 計算Y軸的範圍，以1000為單位調整scale
    min_val = trend_df['總市值'].min()
    max_val = trend_df['總市值'].max()
    
    # 向下取整到最近的1000
    y_min = (min_val // 1000) * 1000
    # 向上取整到最近的1000  
    y_max = ((max_val // 1000) + 1) * 1000
    
    # 如果範圍太小，強制設定最小範圍
    if y_max - y_min < 5000:
        center = (y_min + y_max) / 2
        y_min = center - 2500
        y_max = center + 2500
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=trend_df['日期'],
        y=trend_df['總市值'],
        mode='lines+markers',
        name='總資產價值',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8, color='#3498db'),
        fill='tonexty',
        fillcolor='rgba(52, 152, 219, 0.1)',
        hovertemplate='<b>%{x}</b><br>總資產: NT$%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        height=400,
        yaxis_title="資產價值 (NTD)",
        xaxis_title="日期",
        hovermode='x unified',
        showlegend=False,
        yaxis=dict(
            range=[y_min, y_max],
            tickformat=',.0f'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_holdings_table(person, holdings_df):
    """渲染持股表格"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("持股明細")
    
    if holdings_df.empty:
        st.warning("無持股數據")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if person == 'os':
        # 海外投資表格 - 動態處理欄位
        display_df = holdings_df.copy()
        
        # 格式化數字欄位
        for col in display_df.columns:
            if any(keyword in col for keyword in ['價', '成本', '市值', '損益']):
                if 'USD' in col:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x, 'USD'))
                elif 'NTD' in col:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x, 'TWD'))
            elif '率' in col and '%' not in col:
                display_df[col] = display_df[col].apply(format_percentage)
        
        # 設定顏色樣式
        def color_negative_red(val):
            if isinstance(val, str) and ('$-' in val or 'NT$-' in val or val.startswith('-')):
                return 'color: #e74c3c; font-weight: bold'
            elif isinstance(val, str) and ('+' in val and '%' in val):
                return 'color: #27ae60; font-weight: bold'
            return ''
        
        styled_df = display_df.style.applymap(color_negative_red)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    else:
        # 台股表格
        display_df = holdings_df.copy()
        
        # 先格式化數值欄位，再創建標籤欄位
        format_columns = {
            '目前股價': format_stock_price,
            '總持有股數': format_shares,
            '總投入成本': lambda x: format_currency(x, 'TWD'),
            '目前總市值': lambda x: format_currency(x, 'TWD'),
            '未實現損益': lambda x: format_currency(x, 'TWD'),
            '報酬率': format_percentage
        }
        
        # 應用格式化
        for col, formatter in format_columns.items():
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(formatter)
        
        # 創建持股標籤
        display_df['持股標籤'] = display_df['股票代號'] + ' ' + display_df['股票名稱']
        
        # 重新排序欄位
        column_order = ['持股標籤', '總持有股數', '目前股價', '總投入成本', '目前總市值', '未實現損益', '報酬率']
        display_df = display_df[column_order]
        
        # 設定顏色樣式
        def color_negative_red(val):
            if isinstance(val, str) and ('NT$-' in val or val.startswith('-')):
                return 'color: #e74c3c; font-weight: bold'
            elif isinstance(val, str) and ('+' in val and ('%' in val or 'NT in val)):
                return 'color: #27ae60; font-weight: bold'
            return ''
        
        styled_df = display_df.style.applymap(color_negative_red)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # 主標題
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">💎 智慧投資總覽</h1>
        <p class="hero-subtitle">Jason • Rita • 富邦英股 • 實時投資組合管理系統</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 分頁標籤
    tab1, tab2, tab3 = st.tabs(["🚘 Jason定期定額", "👩🏻 Rita定期定額", "🇬🇧 富邦英股總覽"])
    
    with tab1:
        st.markdown("## Jason 定期定額投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="jason_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Jason投資數據..."):
            holdings_df = load_sheet_data('jason', 'holdings')
            dca_df = load_sheet_data('jason', 'dca')
            trend_df = load_sheet_data('jason', 'trend')
        
        if not holdings_df.empty:
            render_summary_cards('jason', holdings_df, dca_df)
            
            if not trend_df.empty:
                render_trend_chart('jason', trend_df)
            
            render_charts('jason', holdings_df)
            render_holdings_table('jason', holdings_df)
        else:
            st.error("無法載入Jason的投資數據，請檢查Google Sheets連接")
    
    with tab2:
        st.markdown("## Rita 定期定額投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="rita_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Rita投資數據..."):
            holdings_df = load_sheet_data('rita', 'holdings')
            dca_df = load_sheet_data('rita', 'dca')
            trend_df = load_sheet_data('rita', 'trend')
        
        if not holdings_df.empty:
            render_summary_cards('rita', holdings_df, dca_df)
            
            if not trend_df.empty:
                render_trend_chart('rita', trend_df)
            
            render_charts('rita', holdings_df)
            render_holdings_table('rita', holdings_df)
        else:
            st.error("無法載入Rita的投資數據，請檢查Google Sheets連接")
    
    with tab3:
        st.markdown("## 富邦英股 海外投資")
        
        # 更新按鈕置於右上角
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 更新數據", key="os_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入海外投資數據..."):
            holdings_df = load_sheet_data('os', 'holdings')
        
        if not holdings_df.empty:
            render_summary_cards('os', holdings_df)
            render_charts('os', holdings_df)
            render_holdings_table('os', holdings_df)
        else:
            st.error("無法載入海外投資數據，請檢查Google Sheets連接")

    # 頁腳
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin-top: 3rem; border-top: 1px solid #e0e0e0; color: #7f8c8d;">
        <p>💡 數據每5分鐘自動更新 | 📊 投資有風險，請謹慎決策</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()