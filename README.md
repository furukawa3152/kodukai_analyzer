# kodukai_analyzer 💰

## 概要
Gspreadを使って、Googleスプレッドシートの「kodukai-db」シートにアクセスし、家計簿データをStreamlitで分析するWebアプリケーションです。

## 機能
- 📊 **月別支出分析**: 月ごとの支出傾向を可視化
- 🏷️ **項目別分析**: 支出項目ごとの統計とグラフ表示
- 🔍 **項目検索**: 特定の文字列を含む項目の検索・分析
- 📅 **時系列分析**: 日別・曜日別の支出パターン分析

## セットアップ

### 1. 仮想環境の作成
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. Google Sheets API認証設定
1. Google Cloud Consoleでプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. サービスアカウントを作成し、JSONキーファイルをダウンロード
4. JSONファイルを `kodukai-project-920c4d3bc21c.json` として保存
5. スプレッドシートをサービスアカウントと共有

### 4. ローカル実行
```bash
streamlit run app.py
```

## Streamlit Cloudデプロイ

### 1. GitHubリポジトリの準備
- 認証ファイル（*.json）は.gitignoreに含まれているため、プッシュされません
- requirements.txtとapp.pyがリポジトリに含まれていることを確認

### 2. Streamlit Cloudでの設定
1. [Streamlit Cloud](https://share.streamlit.io/)にアクセス
2. GitHubリポジトリを接続
3. Secretsセクションで以下を設定：

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account-email@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project.iam.gserviceaccount.com"
```

## ファイル構成
```
kodukai_analyzer/
├── app.py                          # メインアプリケーション
├── gsheet_connector.py             # ローカル用Google Sheets接続
├── gsheet_connector_cloud.py       # Streamlit Cloud用接続
├── requirements.txt                # 依存関係
├── README.md                       # このファイル
├── .streamlit/
│   ├── config.toml                 # Streamlit設定
│   └── secrets.toml.template       # シークレット設定テンプレート
├── .gitignore                      # Git除外設定
└── kodukai-project-*.json          # Google API認証ファイル（除外）
```

## 使用技術
- **Python 3.x**
- **Streamlit**: Webアプリケーションフレームワーク
- **gspread**: Google Sheets API Python ライブラリ
- **pandas**: データ分析・操作
- **plotly**: インタラクティブなグラフ作成
- **matplotlib/seaborn**: 統計グラフ作成

## データ形式
スプレッドシートの「kodukai-db」シートは以下の形式を想定：
- 項目: 支出項目名
- 金額: 支出金額（数値）
- 日時: 支出日時
- 年月: YYYYMM形式の年月

## ライセンス
MIT License
