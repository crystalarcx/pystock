import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# 1. 配置管理 (Configuration Management)
# 將所有硬編碼的配置集中到一個類別中，方便管理和修改。
# ==============================================================================
class ConfigManager:
    """統一管理應用程式的所有配置"""
    
    # 頁面基礎設定
    PAGE_CONFIG = {
        "page_title": "投資總覽儀表板",
        "page_icon": "📈",
        "layout": "wide",
        "initial_sidebar_state": "collapsed"
    }
    
    # Google Sheets API 配置
    SHEET_CONFIGS = {
        'jason': {
            'id': '17qQIU4KMtbTpo_ozguuzKFHf1HHOhuEBanXxCyE8k4M',
            'holdings_range': '總覽與損益!A:I',
            'dca_range': '投資設定!A:E',
            'trend_range': '資產趨勢!A:B'
        },
        'rita': {
            'id': '1ekCpufAJfrzt1cCLsubqLDUMU98_Ol5hTptOV7uXgpw',
            'holdings_range': '總覽與損益!A:I', 
            'dca_range': '投資設定!A:E',
            'trend_range': '資產趨勢!A:B'
        },
        'ed': {
            'id': '1oyG9eKrq57HMBjTWtg4tmKzHQiqc7r-2CWYyhA9ZHNc',
            'holdings_range': '總覽與損益!A:I', 
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
                'range': '總覽與損益!A:M'
            }
        }
    }
    
    # 目標資產配置
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
        {'key': 'ed_overseas', 'icon': '🌐', 'label': 'Ed', 'desc': '海外總覽'},
        {'key': 'asset_allocation', 'icon': '📊', 'label': '資產配置', 'desc': '整體配置'}
    ]

# ==============================================================================
# 2. 樣式管理 (Style Management)
# 將所有CSS樣式代碼封裝在一個類別中，與主邏輯分離。
# ==============================================================================
class StyleManager:
    """管理和應用CSS樣式"""
    
    @staticmethod
    def apply_styles():
        """應用自定義CSS"""
        st.markdown("""
        <style>
            /* ... (此處省略了800多行的CSS代碼，與原檔案相同) ... */
            /* 為了簡潔，這裡省略了原始CSS，實際使用時請將其完整貼入 */
            .main > div {
                padding-top: 1rem;
            }
            .hero-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 3rem 2rem; border-radius: 20px;
                margin-bottom: 2rem; text-align: center;
            }
            .hero-title { font-size: 3rem; font-weight: 700; }
            .metric-card {
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                border: 1px solid rgba(0,0,0,0.05); padding: 2rem;
                border-radius: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
                text-align: center; margin-bottom: 1.5rem;
            }
            /* ... 更多樣式 ... */
        </style>
        """, unsafe_allow_html=True)


# ==============================================================================
# 3. 數據處理模組 (Data Processing Module)
# 負責所有數據的載入、處理、計算和快取。
# ==============================================================================
class DataManager:
    """處理所有數據相關操作，包括API連接、數據獲取和計算"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.service = self._get_google_sheets_service()

    @st.cache_resource
    def _get_google_sheets_service(_self):
        """取得Google Sheets服務實例 (使用_self避免st.cache_resource的限制)"""
        try:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_info)
            scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets'])
            return build('sheets', 'v4', credentials=scoped_creds)
        except Exception as e:
            st.error(f"Google Sheets API 設置失敗: {e}")
            return None

    @st.cache_data(ttl=3600)  # 快取1小時
    def get_usd_twd_rate(_self):
        """取得USDTWD匯率"""
        try:
            ticker = yf.Ticker("USDTWD=X")
            today_data = ticker.history(period="1d")
            return today_data['Close'].iloc[-1] if not today_data.empty else 31.5
        except Exception:
            return 31.5

    @st.cache_data(ttl=600) # 快取10分鐘
    def load_sheet_data(_self, person, data_type, broker=None):
        """從Google Sheets載入並解析數據"""
        if not _self.service:
            return pd.DataFrame()
        
        try:
            # ... (此處的數據載入邏輯與原檔案的 load_sheet_data 相同) ...
            # 為了簡潔，省略了詳細的實現，實際使用時請將其完整貼入
            return pd.DataFrame() # 替換為完整的函數邏輯
        except Exception as e:
            st.error(f"載入 {person} {broker or data_type} 數據失敗: {e}")
            return pd.DataFrame()
    
    def load_all_data_parallel(self, data_sources):
        """
        並行載入多個Google Sheet數據，提高性能。
        :param data_sources: 一個元組列表，格式為 (('jason', 'holdings'), ('rita', 'dca'))
        """
        results = {}
        with st.spinner("🚀 正在從Google Sheets同步數據..."):
            with ThreadPoolExecutor(max_workers=len(data_sources)) as executor:
                # 建立 future 到 key 的映射
                future_to_key = {
                    executor.submit(self.load_sheet_data, *params): params
                    for params in data_sources
                }
                
                for future in future_to_key:
                    key = future_to_key[future]
                    try:
                        results[key] = future.result()
                    except Exception as exc:
                        st.error(f"載入 {key} 數據時發生錯誤: {exc}")
                        results[key] = pd.DataFrame()
        return results

    def calculate_tw_stock_summary(self, holdings_df):
        """計算台股投資組合的摘要指標"""
        if holdings_df.empty:
            return 0, 0, 0, 0
        total_cost = holdings_df['總投入成本'].sum()
        total_value = holdings_df['目前總市值'].sum()
        total_pl = holdings_df['未實現損益'].sum()
        total_return = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        return total_cost, total_value, total_pl, total_return

    def calculate_asset_allocation(self, all_data):
        """
        計算整體資產配置。
        :param all_data: 包含所有已載入數據的字典
        """
        # ... (此處的資產配置計算邏輯與原檔案的 get_asset_allocation_data 相同) ...
        # 為了簡潔，省略了詳細的實現，實際使用時請將其完整貼入
        allocation_data = {cat: {'value_twd': 0.0, 'percentage': 0.0} for cat in self.config.TARGET_ALLOCATION.keys()}
        total_value = 0 # 替換為完整的計算邏輯
        usd_twd_rate = self.get_usd_twd_rate()
        return allocation_data, total_value, usd_twd_rate

# ==============================================================================
# 4. 圖表生成模組 (Chart Generation Module)
# 專門負責生成所有Plotly圖表。
# ==============================================================================
class ChartManager:
    """管理所有圖表的生成"""

    def create_allocation_comparison_chart(self, categories, target, actual):
        """生成目標 vs 實際資產配置比較圖"""
        fig = go.Figure()
        fig.add_trace(go.Bar(name='目標配置', x=categories, y=target, marker_color='rgba(52, 152, 219, 0.7)'))
        fig.add_trace(go.Bar(name='實際配置', x=categories, y=actual, marker_color='rgba(231, 76, 60, 0.7)'))
        fig.update_layout(title='目標 vs 實際配置比較', barmode='group', template="plotly_white")
        return fig

    def create_pie_chart(self, df, value_col, name_col, title):
        """生成一個通用的圓餅圖"""
        df_filtered = df[df[value_col] > 0]
        fig = px.pie(
            df_filtered, values=value_col, names=name_col, title=title,
            hole=0.4, color_discrete_sequence=px.colors.sequential.Agsunset
        )
        fig.update_traces(textinfo='percent+label', pull=[0.05] * len(df_filtered))
        return fig

# ==============================================================================
# 5. UI組件模組 (UI Components Module)
# 負責渲染所有Streamlit的UI元素，如按鈕、卡片、表格等。
# ==============================================================================
class UIManager:
    """管理所有Streamlit UI組件的渲染"""

    def __init__(self, config_manager, chart_manager):
        self.config = config_manager
        self.charts = chart_manager

    def render_header(self):
        """渲染頁面標題和刷新按鈕"""
        st.markdown('<div class="hero-section"><h1 class="hero-title">📈 投資儀表板</h1><p class="hero-subtitle">快速掌握個人資產概況與趨勢</p></div>', unsafe_allow_html=True)
        if st.button('🔄 更新所有數據', key='refresh_button'):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

    def render_user_selection(self):
        """渲染使用者選擇按鈕"""
        if 'selected_person' not in st.session_state:
            st.session_state.selected_person = 'jason'
        
        cols = st.columns(len(self.config.USER_OPTIONS))
        for i, option in enumerate(self.config.USER_OPTIONS):
            with cols[i]:
                if st.button(f"{option['icon']} {option['label']}", key=f"btn_{option['key']}", use_container_width=True, help=option['desc']):
                    st.session_state.selected_person = option['key']
        return st.session_state.selected_person

    def render_summary_cards(self, total_cost, total_value, total_pl, total_return):
        """渲染台股摘要卡片"""
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總投入成本", f"NT$ {total_cost:,.0f}")
        with col2:
            st.metric("目前總市值", f"NT$ {total_value:,.0f}")
        with col3:
            st.metric("未實現損益", f"NT$ {total_pl:,.0f}", f"{total_return:.2f}%")
    
    def render_holdings_table(self, df):
        """渲染持股明細表格"""
        st.dataframe(df.style.format({
            '目前股價': "{:.2f}",
            '總持有股數': "{:,.0f}",
            '總投入成本': "NT${:,.0f}",
            '目前總市值': "NT${:,.0f}",
            '未實現損益': "NT${:,.0f}",
            '報酬率': "{:,.2f}%"
        }), use_container_width=True)

    def display_asset_allocation_page(self, data_manager):
        """渲染資產配置頁面"""
        st.header("📊 整體資產配置分析")
        
        # 實現數據預載入：一次性並行載入所有需要的數據
        required_data = [
            ('rita', 'holdings'), ('ed', 'holdings'),
            ('ed_overseas', 'schwab'), ('ed_overseas', 'cathay'),
            ('ed_overseas', 'fubon_uk')
        ]
        all_data = data_manager.load_all_data_parallel(required_data)
        
        allocation_data, total_value, _ = data_manager.calculate_asset_allocation(all_data)

        if total_value > 0:
            # ... (渲染資產配置摘要和圖表的邏輯) ...
            pass
        else:
            st.warning("無法取得資產配置數據，請檢查數據來源。")

    def display_tw_stock_page(self, person, data_manager):
        """渲染個人台股投資頁面"""
        st.header(f"{person.capitalize()} 台股投資總覽")
        
        # 並行載入此人需要的數據
        required_data = [(person, 'holdings'), (person, 'dca'), (person, 'trend')]
        loaded_data = data_manager.load_all_data_parallel(required_data)
        
        holdings_df = loaded_data.get((person, 'holdings'), pd.DataFrame())

        if not holdings_df.empty:
            summary_data = data_manager.calculate_tw_stock_summary(holdings_df)
            self.render_summary_cards(*summary_data)
            
            tab1, tab2, tab3 = st.tabs(["📈 持股明細", "🥧 資產配置", "📊 資產趨勢"])
            with tab1:
                self.render_holdings_table(holdings_df)
            with tab2:
                fig = self.charts.create_pie_chart(holdings_df, '目前總市值', '股票名稱', '資產配置 (按市值)')
                st.plotly_chart(fig, use_container_width=True)
            with tab3:
                # ... 渲染趨勢圖 ...
                pass
        else:
            st.warning(f"無法載入 {person} 的投資數據，或數據為空。")

# ==============================================================================
# 6. 主應用程式 (Main Application)
# 負責組織和協調所有模組，控制應用程式的流程。
# ==============================================================================
class InvestmentDashboardApp:
    """主應用程式類，協調所有組件"""

    def __init__(self):
        self.config = ConfigManager()
        st.set_page_config(**self.config.PAGE_CONFIG)
        self.styles = StyleManager()
        self.data_manager = DataManager(self.config)
        self.chart_manager = ChartManager()
        self.ui_manager = UIManager(self.config, self.chart_manager)

    def run(self):
        """執行應用程式的主要邏輯"""
        self.styles.apply_styles()
        self.ui_manager.render_header()
        
        selected_person = self.ui_manager.render_user_selection()
        
        st.markdown("---")

        if selected_person == 'asset_allocation':
            self.ui_manager.display_asset_allocation_page(self.data_manager)
        
        elif selected_person == 'ed_overseas':
            # ... (此處放置渲染 Ed 海外投資頁面的邏輯) ...
            st.header("Ed 海外投資總覽")
            st.info("此區塊正在開發中...")

        else: # jason, rita, ed
            self.ui_manager.display_tw_stock_page(selected_person, self.data_manager)


if __name__ == "__main__":
    app = InvestmentDashboardApp()
    app.run()
