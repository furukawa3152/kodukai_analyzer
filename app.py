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
try:
    # Streamlit Cloud環境の場合
    if "gcp_service_account" in st.secrets:
        from gsheet_connector_cloud import GSheetConnectorCloud as GSheetConnector
    else:
        # ローカル環境の場合
        from gsheet_connector import GSheetConnector
except:
    # ローカル環境用のコネクターを使用
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
        # Streamlit Cloud環境の場合はsecretsから、ローカル環境の場合はハードコーディングされたURLを使用
        try:
            if "SPREADSHEET_URL" in st.secrets:
                spreadsheet_url = st.secrets["SPREADSHEET_URL"]
                worksheet_name = st.secrets.get("WORKSHEET_NAME", "kodukai-db")
            else:
                # ローカル環境用のデフォルト値
                spreadsheet_url = "https://docs.google.com/spreadsheets/d/1reQxe-5Bul3daaEsgnzDXptNxX0rNX844jP8RkAnhVQ/edit?gid=0#gid=0"
                worksheet_name = "kodukai-db"
        except:
            # secretsが利用できない場合（ローカル環境）
            spreadsheet_url = "https://docs.google.com/spreadsheets/d/1reQxe-5Bul3daaEsgnzDXptNxX0rNX844jP8RkAnhVQ/edit?gid=0#gid=0"
            worksheet_name = "kodukai-db"
        
        if connector.open_spreadsheet(spreadsheet_url):
            if connector.select_worksheet(worksheet_name):
                df = connector.get_data_as_dataframe()
                
                if not df.empty:
                    # カラム名を適切に設定
                    if len(df.columns) >= 4:
                        df.columns = ['項目', '金額', '日時', '年月']
                        
                        # データ型の変換
                        df['金額'] = pd.to_numeric(df['金額'], errors='coerce')
                        df['日時'] = pd.to_datetime(df['日時'], errors='coerce')
                        
                        # 年月カラム（202311形式）から年と月を抽出
                        df['年月'] = df['年月'].astype(str).str.zfill(6)  # 6桁に統一
                        df['年'] = df['年月'].str[:4]
                        df['月'] = df['年月'].str[4:6]
                        df['年月表示'] = df['年'] + '年' + df['月'] + '月'  # 表示用
                        df['年月日'] = df['日時'].dt.date
                        
                        return df
    
    return pd.DataFrame()

def create_period_selector(df):
    """期間選択ウィジェットを作成"""
    if df.empty:
        return df
    
    st.sidebar.subheader("📅 分析期間選択")
    
    # 期間選択方法
    period_type = st.sidebar.radio(
        "期間選択方法",
        ["全期間", "年月範囲指定", "日付範囲指定", "最近N ヶ月"]
    )
    
    if period_type == "全期間":
        st.sidebar.info("全期間のデータを表示中")
        return df
    
    elif period_type == "年月範囲指定":
        # 利用可能な年月を取得
        available_months = sorted(df['年月'].unique())
        available_display = [f"{month[:4]}年{month[4:6]}月" for month in available_months]
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            start_idx = st.selectbox(
                "開始月",
                range(len(available_months)),
                format_func=lambda x: available_display[x],
                key="start_month"
            )
        
        with col2:
            end_idx = st.selectbox(
                "終了月",
                range(len(available_months)),
                index=len(available_months)-1,
                format_func=lambda x: available_display[x],
                key="end_month"
            )
        
        if start_idx <= end_idx:
            start_month = available_months[start_idx]
            end_month = available_months[end_idx]
            filtered_df = df[(df['年月'] >= start_month) & (df['年月'] <= end_month)]
            
            st.sidebar.success(f"選択期間: {available_display[start_idx]} ～ {available_display[end_idx]}")
            return filtered_df
        else:
            st.sidebar.error("開始月は終了月より前に設定してください")
            return df
    
    elif period_type == "日付範囲指定":
        # 利用可能な日付範囲を取得
        min_date = df['日時'].min().date()
        max_date = df['日時'].max().date()
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            start_date = st.date_input(
                "開始日",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "終了日",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="end_date"
            )
        
        if start_date <= end_date:
            # 日付でフィルタリング
            filtered_df = df[
                (df['日時'].dt.date >= start_date) & 
                (df['日時'].dt.date <= end_date)
            ]
            
            st.sidebar.success(f"選択期間: {start_date} ～ {end_date}")
            return filtered_df
        else:
            st.sidebar.error("開始日は終了日より前に設定してください")
            return df
    
    elif period_type == "最近N ヶ月":
        available_months = sorted(df['年月'].unique())
        
        n_months = st.sidebar.slider(
            "最近何ヶ月分を表示",
            min_value=1,
            max_value=len(available_months),
            value=min(6, len(available_months)),
            key="n_months"
        )
        
        recent_months = available_months[-n_months:]
        filtered_df = df[df['年月'].isin(recent_months)]
        
        st.sidebar.success(f"最近{n_months}ヶ月分を表示中")
        return filtered_df
    
    return df

def create_monthly_analysis(df):
    """月別分析（締め年月基準）"""
    st.subheader("📊 月別支出分析（締め年月基準）")
    st.info("💡 この分析は「年月」カラム（202311形式）の締め年月を基準に集計しています")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 年月（締め月）別集計
    monthly_summary = df.groupby(['年月', '年月表示']).agg({
        '金額': ['sum', 'count', 'mean']
    }).round(2)
    
    monthly_summary.columns = ['総支出', '支出回数', '平均支出']
    monthly_summary = monthly_summary.reset_index()
    
    # 年月でソート
    monthly_summary = monthly_summary.sort_values('年月')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 月別総支出のグラフ
        fig = px.bar(
            monthly_summary, 
            x='年月表示', 
            y='総支出',
            title='締め月別総支出',
            color='総支出',
            color_continuous_scale='Blues',
            text='総支出'
        )
        fig.update_layout(xaxis_tickangle=-45)
        fig.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 月別支出回数のグラフ
        fig = px.line(
            monthly_summary, 
            x='年月表示', 
            y='支出回数',
            title='締め月別支出回数',
            markers=True,
            text='支出回数'
        )
        fig.update_layout(xaxis_tickangle=-45)
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)
    
    # 統計サマリー
    st.subheader("📈 締め月別統計サマリー")
    
    # 表示用のデータフレームを作成
    display_summary = monthly_summary.copy()
    display_summary['総支出'] = display_summary['総支出'].apply(lambda x: f"¥{x:,.0f}")
    display_summary['平均支出'] = display_summary['平均支出'].apply(lambda x: f"¥{x:,.0f}")
    display_summary = display_summary[['年月表示', '総支出', '支出回数', '平均支出']]
    
    st.dataframe(display_summary, use_container_width=True)
    
    # 追加統計情報
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総期間", f"{len(monthly_summary)} ヶ月")
    
    with col2:
        st.metric("月平均支出", f"¥{monthly_summary['総支出'].mean():,.0f}")
    
    with col3:
        st.metric("最高月支出", f"¥{monthly_summary['総支出'].max():,.0f}")
    
    with col4:
        st.metric("最低月支出", f"¥{monthly_summary['総支出'].min():,.0f}")

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
            
            # 月別推移（締め年月基準）
            monthly_search = filtered_df.groupby(['年月', '年月表示'])['金額'].sum().reset_index()
            monthly_search = monthly_search.sort_values('年月')
            
            if len(monthly_search) > 1:
                fig = px.line(
                    monthly_search, 
                    x='年月表示', 
                    y='金額',
                    title=f"'{search_term}' の締め月別支出推移",
                    markers=True,
                    text='金額'
                )
                fig.update_layout(xaxis_tickangle=-45)
                fig.update_traces(texttemplate='¥%{text:,.0f}', textposition='top center')
                st.plotly_chart(fig, use_container_width=True)
            
            # 詳細データ
            st.subheader("🔍 検索結果詳細")
            display_df = filtered_df[['項目', '金額', '日時', '年月表示']].copy()
            display_df['金額'] = display_df['金額'].apply(lambda x: f"¥{x:,.0f}")
            display_df = display_df.sort_values('日時', ascending=False)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning(f"'{search_term}' を含む項目は見つかりませんでした")

def create_period_comparison(df):
    """期間比較分析"""
    st.subheader("📊 期間比較分析")
    
    if df.empty:
        st.error("データが読み込まれていません")
        return
    
    # 利用可能な年月を取得
    available_months = sorted(df['年月'].unique())
    available_display = [f"{month[:4]}年{month[4:6]}月" for month in available_months]
    
    if len(available_months) < 2:
        st.warning("期間比較には最低2ヶ月分のデータが必要です")
        return
    
    st.write("2つの期間を選択して支出を比較できます")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("期間A")
        a_start_idx = st.selectbox(
            "開始月 (期間A)",
            range(len(available_months)),
            format_func=lambda x: available_display[x],
            key="a_start"
        )
        a_end_idx = st.selectbox(
            "終了月 (期間A)",
            range(len(available_months)),
            index=min(a_start_idx + 2, len(available_months) - 1),
            format_func=lambda x: available_display[x],
            key="a_end"
        )
    
    with col2:
        st.subheader("期間B")
        b_start_idx = st.selectbox(
            "開始月 (期間B)",
            range(len(available_months)),
            index=max(0, len(available_months) - 3),
            format_func=lambda x: available_display[x],
            key="b_start"
        )
        b_end_idx = st.selectbox(
            "終了月 (期間B)",
            range(len(available_months)),
            index=len(available_months) - 1,
            format_func=lambda x: available_display[x],
            key="b_end"
        )
    
    if a_start_idx <= a_end_idx and b_start_idx <= b_end_idx:
        # 期間Aのデータ
        a_months = available_months[a_start_idx:a_end_idx+1]
        df_a = df[df['年月'].isin(a_months)]
        
        # 期間Bのデータ
        b_months = available_months[b_start_idx:b_end_idx+1]
        df_b = df[df['年月'].isin(b_months)]
        
        # 比較統計
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_a = df_a['金額'].sum()
            total_b = df_b['金額'].sum()
            diff = total_b - total_a
            diff_pct = ((total_b - total_a) / total_a * 100) if total_a > 0 else 0
            
            st.metric(
                "総支出比較",
                f"¥{total_b:,}",
                f"¥{diff:+,} ({diff_pct:+.1f}%)"
            )
        
        with col2:
            avg_a = df_a['金額'].mean()
            avg_b = df_b['金額'].mean()
            avg_diff = avg_b - avg_a
            avg_diff_pct = ((avg_b - avg_a) / avg_a * 100) if avg_a > 0 else 0
            
            st.metric(
                "平均支出比較",
                f"¥{avg_b:,.0f}",
                f"¥{avg_diff:+,.0f} ({avg_diff_pct:+.1f}%)"
            )
        
        with col3:
            count_a = len(df_a)
            count_b = len(df_b)
            count_diff = count_b - count_a
            count_diff_pct = ((count_b - count_a) / count_a * 100) if count_a > 0 else 0
            
            st.metric(
                "支出回数比較",
                f"{count_b:,}回",
                f"{count_diff:+,}回 ({count_diff_pct:+.1f}%)"
            )
        
        # 項目別比較
        st.subheader("項目別支出比較（上位10項目）")
        
        # 期間Aの項目別集計
        cat_a = df_a.groupby('項目')['金額'].sum().sort_values(ascending=False).head(10)
        # 期間Bの項目別集計
        cat_b = df_b.groupby('項目')['金額'].sum().sort_values(ascending=False).head(10)
        
        # 共通項目を取得
        common_items = set(cat_a.index) & set(cat_b.index)
        
        if common_items:
            comparison_data = []
            for item in common_items:
                comparison_data.append({
                    '項目': item,
                    f'期間A ({available_display[a_start_idx]}～{available_display[a_end_idx]})': cat_a.get(item, 0),
                    f'期間B ({available_display[b_start_idx]}～{available_display[b_end_idx]})': cat_b.get(item, 0),
                    '差額': cat_b.get(item, 0) - cat_a.get(item, 0)
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('差額', key=abs, ascending=False)
            
            # 表示用にフォーマット
            display_df = comparison_df.copy()
            for col in display_df.columns[1:]:
                if col != '項目':
                    display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("選択した期間に共通する項目がありません")
    
    else:
        st.error("各期間で開始月は終了月より前に設定してください")

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
    
    # 期間選択機能
    filtered_df = create_period_selector(df)
    
    # フィルタ後のデータ概要
    st.sidebar.subheader("📈 データ概要")
    st.sidebar.write(f"総データ数: {len(filtered_df):,} 件")
    st.sidebar.write(f"総支出額: ¥{filtered_df['金額'].sum():,}")
    
    if not filtered_df.empty:
        st.sidebar.write(f"記録期間: {filtered_df['日時'].min().strftime('%Y-%m-%d')} ～ {filtered_df['日時'].max().strftime('%Y-%m-%d')}")
        
        # 締め年月の範囲
        unique_months = sorted(filtered_df['年月'].unique())
        if len(unique_months) > 0:
            start_month = unique_months[0]
            end_month = unique_months[-1]
            start_display = f"{start_month[:4]}年{start_month[4:6]}月"
            end_display = f"{end_month[:4]}年{end_month[4:6]}月"
            st.sidebar.write(f"締め年月: {start_display} ～ {end_display}")
            st.sidebar.write(f"対象月数: {len(unique_months)} ヶ月")
    
    # 分析タイプ選択
    analysis_type = st.sidebar.selectbox(
        "分析タイプを選択",
        ["月別分析", "項目別分析", "項目検索", "時系列分析", "期間比較"]
    )
    
    # データ更新ボタン
    if st.sidebar.button("🔄 データを更新"):
        st.cache_data.clear()
        st.rerun()
    
    # 選択された分析を実行（フィルタされたデータを使用）
    if analysis_type == "月別分析":
        create_monthly_analysis(filtered_df)
    elif analysis_type == "項目別分析":
        create_category_analysis(filtered_df)
    elif analysis_type == "項目検索":
        create_search_analysis(filtered_df)
    elif analysis_type == "時系列分析":
        create_time_analysis(filtered_df)
    elif analysis_type == "期間比較":
        create_period_comparison(df)  # 期間比較は元データを使用

if __name__ == "__main__":
    main()
