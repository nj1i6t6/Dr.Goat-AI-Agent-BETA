#!/bin/bash

# 領頭羊博士 - GitHub Codespaces 部署腳本
# 針對 GitHub Codespaces 環境優化的部署腳本

set -e  # 遇到錯誤立即退出

echo "🐐 領頭羊博士 - GitHub Codespaces 部署 🐐"
echo "========================================"

# 檢查是否在 Codespaces 環境中
if [ "$CODESPACES" == "true" ]; then
    echo "✅ 檢測到 GitHub Codespaces 環境"
else
    echo "⚠️  非 Codespaces 環境，但仍可繼續部署"
fi

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查環境變數檔案
if [ ! -f ".env" ]; then
    echo "⚠️  .env 檔案不存在，從範例檔案創建..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 已從 .env.example 創建 .env 檔案"
    else
        cat > .env << EOF
# 資料庫配置
POSTGRES_DB=goat_nutrition_db
POSTGRES_USER=goat_user
POSTGRES_PASSWORD=goat_password

# Flask 配置
SECRET_KEY=codespaces-development-key-$(date +%s)
FLASK_ENV=development
FLASK_DEBUG=True

# CORS 配置 (Codespaces)
CORS_ORIGINS=https://*.app.github.dev,http://localhost,http://127.0.0.1

# Google Gemini API
GOOGLE_API_KEY=your-gemini-api-key

# 日誌配置
LOG_LEVEL=INFO
EOF
        echo "📝 已創建 .env 檔案（開發模式配置）"
    fi
    echo "🔧 如需修改配置，請編輯 .env 檔案"
fi

echo "✅ 環境檢查完成"

# 清理舊容器和映像
echo "🧹 清理舊容器..."
docker-compose down --remove-orphans 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# 建置映像檔
echo "🔨 建置映像檔..."
docker-compose build --no-cache

# 啟動服務
echo "🚀 啟動服務..."
docker-compose up -d

# 等待資料庫啟動
echo "⏳ 等待資料庫啟動..."
sleep 20

# 檢查資料庫狀態
echo "🔍 檢查資料庫狀態..."
for i in {1..30}; do
    if docker-compose exec -T db pg_isready -U goat_user > /dev/null 2>&1; then
        echo "✅ 資料庫已就緒"
        break
    fi
    echo "⏳ 等待資料庫啟動... ($i/30)"
    sleep 2
done

# 執行資料庫遷移
echo "🗃️  執行資料庫遷移..."
docker-compose exec -T backend flask db upgrade || {
    echo "⚠️  資料庫遷移失敗，嘗試初始化..."
    docker-compose exec -T backend flask db init || true
    docker-compose exec -T backend flask db migrate -m "Initial migration" || true
    docker-compose exec -T backend flask db upgrade || true
}

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 等待應用程式完全啟動
echo "⏳ 等待應用程式啟動..."
sleep 15

# 測試應用程式是否正常運行
echo "🧪 測試應用程式連線..."
BACKEND_URL="http://localhost:5001"
FRONTEND_URL="http://localhost"

# 測試後端
if curl -f -s "$BACKEND_URL/api/auth/status" > /dev/null 2>&1; then
    echo "✅ 後端服務啟動成功"
else
    echo "⚠️  後端服務可能未完全啟動，請檢查日誌"
fi

# 測試前端
if curl -f -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo "✅ 前端服務啟動成功"
else
    echo "⚠️  前端服務可能未完全啟動，請檢查日誌"
fi

echo ""
echo "🎉 部署完成！"
echo "========================================"

if [ "$CODESPACES" == "true" ]; then
    # 在 Codespaces 中，使用動態端口
    echo "📱 Codespaces 環境訪問地址："
    echo "   前端應用: 在 'PORTS' 標籤中找到端口 80 的 URL"
    echo "   後端 API: 在 'PORTS' 標籤中找到端口 5001 的 URL"
    echo "   資料庫: localhost:5432 (內部訪問)"
else
    echo "📱 本地環境訪問地址："
    echo "   前端應用: http://localhost"
    echo "   後端 API: http://localhost:5001/api"
    echo "   資料庫: localhost:5432"
fi

echo ""
echo "📊 管理命令："
echo "   查看日誌: docker-compose logs -f"
echo "   停止服務: docker-compose down"
echo "   重新啟動: docker-compose restart"
echo ""
echo "📋 預設管理員帳號："
echo "   帳號: admin"
echo "   密碼: admin123"
echo "   (請在首次登入後立即修改密碼)"
echo ""
echo "🔧 如果遇到問題："
echo "   1. 檢查 .env 檔案配置"
echo "   2. 查看容器日誌: docker-compose logs"
echo "   3. 重新建置: docker-compose build --no-cache"
