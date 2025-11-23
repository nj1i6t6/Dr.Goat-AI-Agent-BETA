#!/bin/bash

# Docker 容器啟動腳本
# 負責初始化資料庫和啟動應用程式

set -e

echo "=== 領頭羊博士 Docker 啟動腳本 ==="

echo "確認 RAG 向量檔..."
python - <<'PY'
from app.rag_loader import ensure_vectors

try:
    ensure_vectors()
except Exception as exc:  # pragma: no cover - defensive startup handling
    print(f"警告：RAG 預載失敗，將降級為無向量模式: {exc}")
PY

# 等待資料庫可用
echo "等待資料庫連線..."
while ! pg_isready -h ${POSTGRES_HOST:-db} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres}; do
    echo "資料庫尚未就緒，等待 2 秒..."
    sleep 2
done

echo "資料庫連線成功！"

# 檢查是否需要初始化資料庫
echo "檢查資料庫狀態..."

# 設定 Flask 應用程式
export FLASK_APP=run.py

# 初始化資料庫遷移目錄（如果不存在）
if [ ! -d "migrations" ]; then
    echo "初始化資料庫遷移目錄..."
    flask db init
fi

# 檢查資料庫連接
echo "檢查資料庫狀態..."

# 設定 Flask 應用程式
export FLASK_APP=run.py

# 簡化：應用程式會自動處理資料庫初始化
echo "資料庫初始化將由應用程式自動處理"

# 檢查是否需要創建預設用戶（可選）
echo "檢查用戶資料..."
python -c "
from app import create_app, db
from app.models import User
import os

app = create_app()
try:
    with app.app_context():
        # 檢查是否有用戶存在
        user_count = User.query.count()
        if user_count == 0:
            print('沒有找到用戶，考慮創建預設管理員帳戶')
            # 可以在這裡創建預設用戶
            # admin_user = User(username='admin')
            # admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            # db.session.add(admin_user)
            # db.session.commit()
            # print('已創建預設管理員帳戶: admin')
        else:
            print(f'資料庫中已有 {user_count} 個用戶')
except Exception as e:
    print(f'檢查用戶時發生錯誤: {e}')
    print('這可能是正常的，如果是第一次啟動的話')
"

echo "資料庫初始化完成！"

# 啟動應用程式
echo "啟動應用程式..."
echo "使用命令: $@"

exec "$@"
