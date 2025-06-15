import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import os

# 環境に応じてコネクターを選択
if "gcp_service_account" in st.secrets:
    from gsheet_connector_cloud import GSheetConnectorCloud as GSheetConnector
else:
    from gsheet_connector import GSheetConnector

# ページ設定
st.set_page_config(
    page_title="こづかい分析アプリ",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 日本語フォント設定（matplotlib用）
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']

@st.cache_data(ttl=300)  # 5分間キャッシュ
def load_data():
    """データを読み込む"""
    connector = GSheetConnector()
    
    if connector.connect():
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1reQxe-5Bul3daaEsgnzDXptNxX0rNX844jP8RkAnhVQ/edit?gid=0#gid=0"
        
        if connector.open_spreadsheet(spreadsheet_url):
            if connector.select_worksheet('kodukai-db'):
                df = connector.get_data_as_dataframe()
                
                if not df.empty:
                    # カラム名を適切に設定
                    if len(df.columns) >= 4:
                        df.columns = ['項目', '金額', '日時', '年月']
                        
                        # データ型の変換
                        df['金額'] = pd.to_numeric(df['金額'], errors='coerce')
                        df['日時'] = pd.to_datetime(df['日時'], errors='coerce')
                        
                        # 年月カラムから年と月を抽出
                        df['年'] = df['年月'].astype(str).str[:4]
                        df['月'] = df['年月'].astype(str).str[4:6]
                        df['年月日'] = df['日時'].dt.date
                        
                        return df
    
    return pd.DataFrame()

def create_monthly_analysis(df):
    """月別分析"""
    st.subheader("📊 月別支出分析")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 月別集計
    monthly_summary = df.groupby('年月').agg({
        '金額': ['sum', 'count', 'mean']
    }).round(2)
    
    monthly_summary.columns = ['総支出', '支出回数', '平均支出']
    monthly_summary = monthly_summary.reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 月別総支出のグラフ
        fig = px.bar(
            monthly_summary, 
            x='年月', 
            y='総支出',
            title='月別総支出',
            color='総支出',
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 月別支出回数のグラフ
        fig = px.line(
            monthly_summary, 
            x='年月', 
            y='支出回数',
            title='月別支出回数',
            markers=True
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # 統計サマリー
    st.subheader("📈 月別統計サマリー")
    st.dataframe(monthly_summary, use_container_width=True)

def create_category_analysis(df):
    """カテゴリ別分析"""
    st.subheader("🏷️ 項目別支出分析")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 項目別集計
    category_summary = df.groupby('項目').agg({
        '金額': ['sum', 'count', 'mean']
    }).round(2)
    
    category_summary.columns = ['総支出', '支出回数', '平均支出']
    category_summary = category_summary.reset_index().sort_values('総支出', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 上位10項目の円グラフ
        top_10 = category_summary.head(10)
        fig = px.pie(
            top_10, 
            values='総支出', 
            names='項目',
            title='支出項目別割合（上位10項目）'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 上位15項目の棒グラフ
        top_15 = category_summary.head(15)
        fig = px.bar(
            top_15, 
            x='総支出', 
            y='項目',
            orientation='h',
            title='項目別総支出（上位15項目）',
            color='総支出',
            color_continuous_scale='Reds'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # 全項目の統計
    st.subheader("📊 全項目統計")
    st.dataframe(category_summary, use_container_width=True)

def create_search_analysis(df):
    """検索機能"""
    st.subheader("🔍 項目検索・分析")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 検索フォーム
    search_term = st.text_input("検索したい項目名を入力してください（部分一致）", "")
    
    if search_term:
        # 検索実行
        filtered_df = df[df['項目'].str.contains(search_term, case=False, na=False)]
        
        if not filtered_df.empty:
            st.success(f"'{search_term}' を含む項目が {len(filtered_df)} 件見つかりました")
            
            # 検索結果の統計
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("総支出", f"¥{filtered_df['金額'].sum():,}")
            
            with col2:
                st.metric("支出回数", f"{len(filtered_df)} 回")
            
            with col3:
                st.metric("平均支出", f"¥{filtered_df['金額'].mean():.0f}")
            
            # 月別推移
            monthly_search = filtered_df.groupby('年月')['金額'].sum().reset_index()
            if len(monthly_search) > 1:
                fig = px.line(
                    monthly_search, 
                    x='年月', 
                    y='金額',
                    title=f"'{search_term}' の月別支出推移",
                    markers=True
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # 詳細データ
            st.subheader("🔍 検索結果詳細")
            st.dataframe(
                filtered_df[['項目', '金額', '日時', '年月']].sort_values('日時', ascending=False),
                use_container_width=True
            )
        else:
            st.warning(f"'{search_term}' を含む項目は見つかりませんでした")

def create_time_analysis(df):
    """時系列分析"""
    st.subheader("📅 時系列分析")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 日別集計
    daily_summary = df.groupby('年月日')['金額'].sum().reset_index()
    daily_summary['年月日'] = pd.to_datetime(daily_summary['年月日'])
    
    # 日別支出の推移
    fig = px.line(
        daily_summary, 
        x='年月日', 
        y='金額',
        title='日別支出推移',
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 曜日別分析
    df_with_weekday = df.copy()
    df_with_weekday['曜日'] = df_with_weekday['日時'].dt.day_name()
    weekday_summary = df_with_weekday.groupby('曜日')['金額'].sum().reset_index()
    
    # 曜日の順序を設定
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_summary['曜日'] = pd.Categorical(weekday_summary['曜日'], categories=weekday_order, ordered=True)
    weekday_summary = weekday_summary.sort_values('曜日')
    
    fig = px.bar(
        weekday_summary, 
        x='曜日', 
        y='金額',
        title='曜日別支出',
        color='金額',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    """メイン関数"""
    st.title("💰 こづかい分析アプリ")
    st.markdown("---")
    
    # データ読み込み
    with st.spinner("データを読み込み中..."):
        df = load_data()
    
    if df.empty:
        st.error("データの読み込みに失敗しました。認証ファイルとスプレッドシートの設定を確認してください。")
        return
    
    # サイドバー
    st.sidebar.title("📊 分析メニュー")
    
    # データ概要
    st.sidebar.subheader("📈 データ概要")
    st.sidebar.write(f"総データ数: {len(df):,} 件")
    st.sidebar.write(f"総支出額: ¥{df['金額'].sum():,}")
    st.sidebar.write(f"期間: {df['日時'].min().strftime('%Y-%m-%d')} ～ {df['日時'].max().strftime('%Y-%m-%d')}")
    
    # 分析タイプ選択
    analysis_type = st.sidebar.selectbox(
        "分析タイプを選択",
        ["月別分析", "項目別分析", "項目検索", "時系列分析"]
    )
    
    # データ更新ボタン
    if st.sidebar.button("🔄 データを更新"):
        st.cache_data.clear()
        st.rerun()
    
    # 選択された分析を実行
    if analysis_type == "月別分析":
        create_monthly_analysis(df)
    elif analysis_type == "項目別分析":
        create_category_analysis(df)
    elif analysis_type == "項目検索":
        create_search_analysis(df)
    elif analysis_type == "時系列分析":
        create_time_analysis(df)

if __name__ == "__main__":
    main()
