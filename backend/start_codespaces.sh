#!/bin/bash
# Codespaces 啟動腳本 - 使用 SQLite
# 這個腳本會覆蓋 PostgreSQL 環境變數，強制使用 SQLite

echo "🚀 準備在 Codespaces 中啟動應用程式..."
echo "📄 設定使用 SQLite 資料庫（覆蓋 .env 中的 PostgreSQL 設定）..."

# 覆蓋 PostgreSQL 環境變數為空值，強制使用 SQLite
export POSTGRES_DB=""
export POSTGRES_USER=""
export POSTGRES_PASSWORD=""
export POSTGRES_HOST=""
export POSTGRES_PORT=""

# 設定 Flask 為開發模式以便調試
export FLASK_DEBUG=True
export FLASK_ENV=development

echo "✅ 環境變數已設定為使用 SQLite"
echo "🔧 檢查資料庫設定..."

# 檢查應用程式配置
python -c "
from app import create_app
app = create_app()
with app.app_context():
    print(f'📊 資料庫 URI: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        print('✅ 成功設定為使用 SQLite')
    else:
        print('❌ 仍在嘗試使用 PostgreSQL')
"

echo "🏃 啟動 Flask 應用程式..."
python run.py
