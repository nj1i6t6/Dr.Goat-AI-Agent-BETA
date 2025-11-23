#!/bin/bash
# 生產模式啟動腳本 - 使用 PostgreSQL

echo "🏭 生產模式啟動..."
echo "📊 使用 PostgreSQL 資料庫"

# 確保使用 .env 檔案中的完整設定
echo "🔧 檢查 PostgreSQL 連接..."

# 檢查應用程式配置
python -c "
from app import create_app
app = create_app()
with app.app_context():
    print(f'📊 資料庫 URI: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        print('✅ 成功設定為使用 PostgreSQL')
    else:
        print('⚠️  使用 SQLite (可能是因為 PostgreSQL 環境變數未設定)')
"

echo "🏃 啟動 Flask 應用程式 (生產模式)..."
python run.py
