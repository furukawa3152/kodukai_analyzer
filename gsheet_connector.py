import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

class GSheetConnector:
    def __init__(self, credentials_file='kodukai-project-920c4d3bc21c.json'):
        """
        Google Sheets APIに接続するためのクラス
        
        Args:
            credentials_file (str): サービスアカウントのJSONファイルパス
        """
        self.credentials_file = credentials_file
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
    def connect(self):
        """Google Sheets APIに接続"""
        try:
            # スコープを定義
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 認証情報を読み込み
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )
            
            # gspreadクライアントを作成
            self.client = gspread.authorize(credentials)
            print("Google Sheets APIに正常に接続しました")
            return True
            
        except Exception as e:
            print(f"接続エラー: {e}")
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
            print(f"スプレッドシートを開く際のエラー: {e}")
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
            print(f"ワークシートを選択する際のエラー: {e}")
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
            print(f"データ取得エラー: {e}")
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

# 使用例とテスト用の関数
def test_connection():
    """接続テスト"""
    connector = GSheetConnector()
    
    # 接続テスト
    if connector.connect():
        # スプレッドシートを開く
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1reQxe-5Bul3daaEsgnzDXptNxX0rNX844jP8RkAnhVQ/edit?gid=0#gid=0"
        
        if connector.open_spreadsheet(spreadsheet_url):
            # ワークシートを選択
            if connector.select_worksheet('kodukai-db'):
                # データを取得
                df = connector.get_data_as_dataframe()
                
                if not df.empty:
                    print("\n=== データの概要 ===")
                    print(f"データ形状: {df.shape}")
                    print(f"カラム: {list(df.columns)}")
                    print("\n=== 最初の5行 ===")
                    print(df.head())
                    
                    return df
    
    return None

if __name__ == "__main__":
    test_connection()
