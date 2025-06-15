import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
import json

class GSheetConnectorCloud:
    def __init__(self):
        """
        Streamlit Cloud用のGoogle Sheets APIコネクター
        """
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
    def connect(self):
        """Google Sheets APIに接続（Streamlit Cloud用）"""
        try:
            # Streamlit Cloudのsecretsから認証情報を取得
            if "gcp_service_account" in st.secrets:
                # スコープを定義
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                # 認証情報を作成
                credentials = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes=scope
                )
                
                # gspreadクライアントを作成
                self.client = gspread.authorize(credentials)
                print("Google Sheets APIに正常に接続しました（Cloud版）")
                return True
            else:
                st.error("認証情報が設定されていません。Streamlit CloudのSecretsを確認してください。")
                return False
                
        except Exception as e:
            st.error(f"接続エラー: {e}")
            return False
    
    def open_spreadsheet(self, spreadsheet_url):
        """
        スプレッドシートを開く
        
        Args:
            spreadsheet_url (str): スプレッドシートのURL
        """
        try:
            # URLからスプレッドシートIDを抽出
            spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            print(f"スプレッドシート '{self.spreadsheet.title}' を開きました")
            return True
            
        except Exception as e:
            st.error(f"スプレッドシートを開く際のエラー: {e}")
            return False
    
    def select_worksheet(self, worksheet_name='kodukai-db'):
        """
        ワークシートを選択
        
        Args:
            worksheet_name (str): ワークシート名
        """
        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
            print(f"ワークシート '{worksheet_name}' を選択しました")
            return True
            
        except Exception as e:
            st.error(f"ワークシートを選択する際のエラー: {e}")
            return False
    
    def get_data_as_dataframe(self):
        """
        ワークシートのデータをPandas DataFrameとして取得
        
        Returns:
            pd.DataFrame: スプレッドシートのデータ
        """
        try:
            # 全データを取得
            data = self.worksheet.get_all_records()
            
            # DataFrameに変換
            df = pd.DataFrame(data)
            
            print(f"データを取得しました: {len(df)} 行, {len(df.columns)} 列")
            return df
            
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            return pd.DataFrame()
    
    def get_worksheet_info(self):
        """ワークシートの基本情報を取得"""
        if self.worksheet:
            return {
                'title': self.worksheet.title,
                'row_count': self.worksheet.row_count,
                'col_count': self.worksheet.col_count
            }
        return None
