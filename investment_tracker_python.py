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
    page_title="定期定額總覽",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        color: #6c757d;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3498db !important;
        color: white !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    
    .metric-change {
        font-size: 0.8rem;
        opacity: 0.8;
    }
    
    .profit { color: #27ae60; }
    .loss { color: #e74c3c; }
    
    .dca-card {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .dca-item {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

class InvestmentTracker:
    def __init__(self):
        self.service = None
        self.setup_google_sheets()
        
        # Google Sheets IDs 和範圍
        self.SHEET_CONFIGS = {
            'jason': {
                'id': '1Q0ZOzpAWlnoXgbD8B58PYwbIDuLdKTHgKDYRFVD8CVmzox5iYfSuCpgx7FA5zyWncKhXvOegdlT7SM',
                'holdings_range': 'holdings!A:H',
                'dca_range': 'DCA!A:E',
                'trend_range': 'trend!A:B'
            },
            'rita': {
                'id': '1SA0SRsn13OXA07qb9KvUNHZIhsuejDBxcWSCYcMHaSd3QfPZVhJ84942K_zqx1nEtZpOllKKxpDIU5',
                'holdings_range': 'holdings!A:H', 
                'dca_range': 'DCA!A:E',
                'trend_range': 'trend!A:B'
            },
            'os': {
                'id': '1RLh_tEC6tU48fIQsBv6RoFFVj2jZggf8eD2TL2DcKksWzvXBSm1oMtq4OzNlJWrvoiDfti8RQPki2L',
                'holdings_range': 'holdings!A:L'
            }
        }

    def setup_google_sheets(self):
        """設置Google Sheets API連接"""
        try:
            # 從Streamlit secrets或本地檔案讀取憑證
            if "google_credentials" in st.secrets:
                credentials_info = dict(st.secrets["google_credentials"])
                credentials = Credentials.from_service_account_info(credentials_info)
            else:
                # 嘗試從本地檔案讀取
                credentials = Credentials.from_service_account_file('credentials.json')
            
            # 設置必要的權限範圍
            scoped_credentials = credentials.with_scopes([
                'https://www.googleapis.com/auth/spreadsheets.readonly'
            ])
            
            self.service = build('sheets', 'v4', credentials=scoped_credentials)
        except Exception as e:
            st.error(f"Google Sheets API 設置失敗: {e}")
            st.info("請確認 credentials.json 檔案存在且格式正確，或在 Streamlit secrets 中設定憑證")

    def parse_number(self, value):
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

    def load_sheet_data(self, person, data_type):
        """從Google Sheets載入數據"""
        if not self.service:
            return pd.DataFrame()
        
        try:
            config = self.SHEET_CONFIGS[person]
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
            result = self.service.spreadsheets().values().get(
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
                # 海外投資數據處理
                numeric_columns = [
                    '目前美價', '總持有股數', '總投入成本(USD)', 
                    '目前總市值(USD)', '目前總市值(NTD)', '未實現損益(USD)', 
                    '未實現報酬率', '投資損益(不計匯差,NTD)', 
                    '匯率損益(NTD)', '總未實現損益(計算匯差,NTD)', '總未實現損益%'
                ]
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
                    df[col] = df[col].apply(self.parse_number)
            
            return df
            
        except Exception as e:
            st.error(f"載入{person} {data_type}數據失敗: {e}")
            return pd.DataFrame()

    def format_currency(self, amount, currency='TWD'):
        """格式化貨幣"""
        if currency == 'USD':
            return f"${amount:,.0f}"
        else:
            return f"NT${amount:,.0f}"

    def format_percentage(self, value):
        """格式化百分比"""
        return f"{'+' if value > 0 else ''}{value:.2f}%"

    def render_summary_cards(self, person, holdings_df, dca_df=None):
        """渲染摘要卡片"""
        if person == 'os':
            # 海外投資摘要
            total_cost_usd = holdings_df['總投入成本(USD)'].sum()
            total_value_usd = holdings_df['目前總市值(USD)'].sum()
            total_value_ntd = holdings_df['目前總市值(NTD)'].sum()
            total_pl_usd = holdings_df['未實現損益(USD)'].sum()
            investment_pl_ntd = holdings_df['投資損益(不計匯差,NTD)'].sum()
            fx_pl_ntd = holdings_df['匯率損益(NTD)'].sum()
            total_pl_ntd = holdings_df['總未實現損益(計算匯差,NTD)'].sum()
            
            return_rate_usd = (total_pl_usd / total_cost_usd) * 100 if total_cost_usd > 0 else 0
            return_rate_ntd = (total_pl_ntd / (total_value_ntd - total_pl_ntd)) * 100 if total_value_ntd > total_pl_ntd else 0
            
            col1, col2, col3 = st.columns(3)
            col4, col5 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">投資成本 (美元)</div>
                    <div class="metric-value">{self.format_currency(total_cost_usd, 'USD')}</div>
                    <div class="metric-change">持股檔數: {len(holdings_df)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">目前市值</div>
                    <div class="metric-value">{self.format_currency(total_value_usd, 'USD')}</div>
                    <div class="metric-change">{self.format_currency(total_value_ntd, 'TWD')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                profit_class = 'profit' if total_pl_usd >= 0 else 'loss'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">投資損益 (美元)</div>
                    <div class="metric-value {profit_class}">{self.format_currency(total_pl_usd, 'USD')}</div>
                    <div class="metric-change">{self.format_percentage(return_rate_usd)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                fx_class = 'profit' if fx_pl_ntd >= 0 else 'loss'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">匯率損益 (台幣)</div>
                    <div class="metric-value {fx_class}">{self.format_currency(fx_pl_ntd, 'TWD')}</div>
                    <div class="metric-change">匯率波動影響</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                total_class = 'profit' if total_pl_ntd >= 0 else 'loss'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">總損益 (台幣)</div>
                    <div class="metric-value {total_class}">{self.format_currency(total_pl_ntd, 'TWD')}</div>
                    <div class="metric-change">{self.format_percentage(return_rate_ntd)}</div>
                </div>
                """, unsafe_allow_html=True)
        
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
                    <div class="metric-value">{self.format_currency(total_cost)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">目前市值</div>
                    <div class="metric-value">{self.format_currency(total_value)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                profit_class = 'profit' if total_pl >= 0 else 'loss'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">未實現損益</div>
                    <div class="metric-value {profit_class}">{self.format_currency(total_pl)}</div>
                    <div class="metric-change">{self.format_percentage(total_return)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                if dca_df is not None and not dca_df.empty:
                    st.markdown(f"""
                    <div class="dca-card">
                        <div class="metric-label">📅 定期定額設定</div>
                        <div style="font-size: 0.9rem; margin-top: 10px;">
                            {"".join([f'''
                            <div class="dca-item">
                                <strong>{row["股票代號"]} {row["股票名稱"]}</strong><br>
                                <small>每月{self.format_currency(row["每月投入金額"])} | {int(row["扣款日"])}號扣款</small>
                            </div>
                            ''' for _, row in dca_df.iterrows()])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="dca-card">
                        <div class="metric-label">📅 定期定額設定</div>
                        <div style="text-align: center; opacity: 0.8; margin-top: 10px;">暫無設定資料</div>
                    </div>
                    """, unsafe_allow_html=True)

    def render_charts(self, person, holdings_df):
        """渲染圖表"""
        if holdings_df.empty:
            st.warning("無數據可顯示圖表")
            return
        
        if person == 'os':
            # 海外投資圖表
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("投資組合分布 (USD)")
                fig_portfolio = px.pie(
                    values=holdings_df['目前總市值(USD)'],
                    names=holdings_df['股票名稱'],
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_portfolio.update_traces(textposition='inside', textinfo='percent+label')
                fig_portfolio.update_layout(height=400)
                st.plotly_chart(fig_portfolio, use_container_width=True)
            
            with col2:
                st.subheader("投資損益分析")
                fig_pl = px.bar(
                    x=holdings_df['股票名稱'],
                    y=holdings_df['未實現損益(USD)'],
                    color=holdings_df['未實現損益(USD)'],
                    color_continuous_scale=['red', 'green'],
                    color_continuous_midpoint=0
                )
                fig_pl.update_layout(
                    height=400,
                    yaxis_title="損益 (USD)",
                    xaxis_title="股票",
                    showlegend=False
                )
                st.plotly_chart(fig_pl, use_container_width=True)
            
            # 匯率影響分析
            st.subheader("匯率影響分析")
            fig_fx = go.Figure()
            
            fig_fx.add_trace(go.Bar(
                name='投資損益 (不計匯差)',
                x=holdings_df['股票名稱'],
                y=holdings_df['投資損益(不計匯差,NTD)'],
                marker_color='lightblue'
            ))
            
            fig_fx.add_trace(go.Bar(
                name='匯率損益',
                x=holdings_df['股票名稱'],
                y=holdings_df['匯率損益(NTD)'],
                marker_color='orange'
            ))
            
            fig_fx.add_trace(go.Bar(
                name='總損益',
                x=holdings_df['股票名稱'],
                y=holdings_df['總未實現損益(計算匯差,NTD)'],
                marker_color='green'
            ))
            
            fig_fx.update_layout(
                barmode='group',
                height=400,
                yaxis_title="損益 (NTD)",
                xaxis_title="股票"
            )
            st.plotly_chart(fig_fx, use_container_width=True)
        
        else:
            # 台股圖表
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("投資組合分布")
                holdings_df['股票標籤'] = holdings_df['股票代號'] + ' ' + holdings_df['股票名稱']
                fig_portfolio = px.pie(
                    values=holdings_df['目前總市值'],
                    names=holdings_df['股票標籤'],
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_portfolio.update_traces(textposition='inside', textinfo='percent+label')
                fig_portfolio.update_layout(height=400)
                st.plotly_chart(fig_portfolio, use_container_width=True)
            
            with col2:
                st.subheader("損益分析")
                fig_pl = px.bar(
                    x=holdings_df['股票標籤'],
                    y=holdings_df['未實現損益'],
                    color=holdings_df['未實現損益'],
                    color_continuous_scale=['red', 'green'],
                    color_continuous_midpoint=0
                )
                fig_pl.update_layout(
                    height=400,
                    yaxis_title="損益 (NTD)",
                    xaxis_title="股票",
                    showlegend=False
                )
                st.plotly_chart(fig_pl, use_container_width=True)

    def render_trend_chart(self, person, trend_df):
        """渲染資產趨勢圖表"""
        if trend_df.empty:
            return
        
        st.subheader("📈 資產趨勢變化")
        
        # 計算變化
        trend_df['變化金額'] = trend_df['總市值'].diff()
        trend_df['變化百分比'] = trend_df['總市值'].pct_change() * 100
        
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
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_holdings_table(self, person, holdings_df):
        """渲染持股表格"""
        st.subheader("持股明細")
        
        if holdings_df.empty:
            st.warning("無持股數據")
            return
        
        if person == 'os':
            # 海外投資表格
            display_df = holdings_df.copy()
            
            # 格式化數字欄位
            format_columns = {
                '目前美價': lambda x: self.format_currency(x, 'USD'),
                '總投入成本(USD)': lambda x: self.format_currency(x, 'USD'),
                '目前總市值(USD)': lambda x: self.format_currency(x, 'USD'),
                '目前總市值(NTD)': lambda x: self.format_currency(x, 'TWD'),
                '未實現損益(USD)': lambda x: self.format_currency(x, 'USD'),
                '未實現報酬率': lambda x: self.format_percentage(x),
                '投資損益(不計匯差,NTD)': lambda x: self.format_currency(x, 'TWD'),
                '匯率損益(NTD)': lambda x: self.format_currency(x, 'TWD'),
                '總未實現損益(計算匯差,NTD)': lambda x: self.format_currency(x, 'TWD'),
                '總未實現損益%': lambda x: self.format_percentage(x)
            }
            
            for col, formatter in format_columns.items():
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(formatter)
            
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
            display_df['持股標籤'] = display_df['股票代號'] + ' ' + display_df['股票名稱']
            
            # 重新排序欄位
            column_order = ['持股標籤', '總持有股數', '目前股價', '總投入成本', '目前總市值', '未實現損益', '報酬率']
            display_df = display_df[column_order]
            
            # 格式化
            format_columns = {
                '目前股價': lambda x: self.format_currency(x, 'TWD'),
                '總投入成本': lambda x: self.format_currency(x, 'TWD'),
                '目前總市值': lambda x: self.format_currency(x, 'TWD'),
                '未實現損益': lambda x: self.format_currency(x, 'TWD'),
                '報酬率': lambda x: self.format_percentage(x)
            }
            
            for col, formatter in format_columns.items():
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(formatter)
            
            # 設定顏色樣式
            def color_negative_red(val):
                if isinstance(val, str) and ('NT$-' in val or val.startswith('-')):
                    return 'color: #e74c3c; font-weight: bold'
                elif isinstance(val, str) and ('+' in val):
                    return 'color: #27ae60; font-weight: bold'
                return ''
            
            styled_df = display_df.style.applymap(color_negative_red)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

def main():
    # 主標題
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(45deg, #2c3e50, #3498db); color: white; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">📊 定期定額總覽</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Jason • Rita • 富邦英股</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化追蹤器
    tracker = InvestmentTracker()
    
    # 側邊欄控制
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        if st.button("🔄 重新整理所有數據", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.info("💡 數據會自動從Google Sheets同步更新")
    
    # 分頁標籤
    tab1, tab2, tab3 = st.tabs(["🚘 Jason定期定額", "👩🏻 Rita定期定額", "🇬🇧 富邦英股總覽"])
    
    with tab1:
        st.header("Jason 定期定額投資")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📄 更新Jason資料", key="jason_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Jason投資數據..."):
            holdings_df = load_data_cached(tracker, 'jason', 'holdings')
            dca_df = load_data_cached(tracker, 'jason', 'dca')
            trend_df = load_data_cached(tracker, 'jason', 'trend')
        
        if not holdings_df.empty:
            tracker.render_summary_cards('jason', holdings_df, dca_df)
            
            if not trend_df.empty:
                tracker.render_trend_chart('jason', trend_df)
            
            tracker.render_charts('jason', holdings_df)
            tracker.render_holdings_table('jason', holdings_df)
        else:
            st.error("無法載入Jason的投資數據，請檢查Google Sheets連接")
    
    with tab2:
        st.header("Rita 定期定額投資")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📄 更新Rita資料", key="rita_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入Rita投資數據..."):
            holdings_df = load_data_cached(tracker, 'rita', 'holdings')
            dca_df = load_data_cached(tracker, 'rita', 'dca')
            trend_df = load_data_cached(tracker, 'rita', 'trend')
        
        if not holdings_df.empty:
            tracker.render_summary_cards('rita', holdings_df, dca_df)
            
            if not trend_df.empty:
                tracker.render_trend_chart('rita', trend_df)
            
            tracker.render_charts('rita', holdings_df)
            tracker.render_holdings_table('rita', holdings_df)
        else:
            st.error("無法載入Rita的投資數據，請檢查Google Sheets連接")
    
    with tab3:
        st.header("富邦英股 海外投資")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📄 更新海外投資資料", key="os_update"):
                st.cache_data.clear()
                st.rerun()
        
        with st.spinner("載入海外投資數據..."):
            holdings_df = load_data_cached(tracker, 'os', 'holdings')
        
        if not holdings_df.empty:
            tracker.render_summary_cards('os', holdings_df)
            tracker.render_charts('os', holdings_df)
            tracker.render_holdings_table('os', holdings_df)
        else:
            st.error("無法載入海外投資數據，請檢查Google Sheets連接")

@st.cache_data(ttl=300)  # 快取5分鐘
def load_data_cached(tracker, person, data_type):
    """快取數據載入函數"""
    return tracker.load_sheet_data(person, data_type)

if __name__ == "__main__":
    main()