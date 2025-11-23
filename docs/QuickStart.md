# 快速開始

> 以下以 **Windows PowerShell** 為例。若使用 macOS/Linux，請改用 `python3`、`cp` 指令並調整路徑格式。

## 1. 準備環境

```powershell
# 專案根目錄
Copy-Item .env.example .env

# 重要環境變數（請於 .env 內填寫）
# - SECRET_KEY：Flask Session 密鑰
# - API_HMAC_SECRET：IoT API Key HMAC 密鑰（至少 32 bytes）
# - GOOGLE_API_KEY：Gemini API Key（若前端未帶 X-Api-Key 時使用）
# - REDIS_PASSWORD、POSTGRES_*：依需求設定

# 後端虛擬環境
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# （可選）若本機無 Redis，可使用 Docker 啟動
$env:REDIS_PASSWORD = "<YOUR_REDIS_PASSWORD>"
docker run --rm -p 6379:6379 redis:7.2-alpine redis-server --requirepass "$REDIS_PASSWORD"

# 前端相依
cd ..\frontend
npm install
```

## 2. 啟動服務

後端（預設使用 SQLite，監聽 http://localhost:5001 ）

```powershell
cd backend
$env:REDIS_PASSWORD = "<YOUR_REDIS_PASSWORD>"
$env:FLASK_ENV = "development"
$env:CORS_ORIGINS = "http://localhost:5173"
python run.py
```

前端（Vite 開發伺服器，監聽 http://localhost:5173 ）

```powershell
cd frontend
npm run dev
```

啟動完成後可檢查：

| 項目 | URL |
|------|-----|
| Vue SPA | http://localhost:5173 |
| 後端 API | http://localhost:5001 |
| Swagger UI | http://localhost:5001/docs |
| Session 健康檢查 | http://localhost:5001/api/auth/status |

## 3. Docker Compose（整合部署）

```powershell
Copy-Item .env.example .env
# 編輯 .env，填入 SECRET_KEY / API_HMAC_SECRET / GOOGLE_API_KEY / POSTGRES_* / REDIS_PASSWORD

docker compose up --build -d
docker compose ps
```

主要服務埠：前端 `3000→80`、後端 `5001`、PostgreSQL `5432`、Redis `6379`、IoT 模擬器 `9000`（隨機）。詳細設定請見 [Deployment](./Deployment.md)。

## 4. 首次試跑 API

```powershell
# 1. 註冊並登入
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/register" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -SessionVariable s
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/login" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -WebSession $s

# 2. 新增羊隻
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/sheep/" -ContentType "application/json" -Body '{"EarNum":"A001","Breed":"台灣黑山羊","Sex":"母","BirthDate":"2024-01-15"}' -WebSession $s

# 3. 建立產品批次並公開
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/traceability/batches" -ContentType "application/json" -Body '{"batch_number":"BATCH-001","product_name":"鮮羊乳 946ml","production_date":"2025-10-04","is_public":true}' -WebSession $s

# 4. 取得儀表板摘要
Invoke-RestMethod -Method Get -Uri "http://localhost:5001/api/dashboard/data" -WebSession $s | ConvertTo-Json -Depth 4

# 5. 建立背景任務
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/tasks/example" -WebSession $s | ConvertTo-Json
```

若要測試 AI 端點或生長預測，請提供 `X-Api-Key: <Gemini API Key>`：

```powershell
$headers = @{ "X-Api-Key" = "<YOUR_GEMINI_API_KEY>" }
Invoke-RestMethod -Method Get -Uri "http://localhost:5001/api/agent/tip" -Headers $headers -WebSession $s
Invoke-RestMethod -Method Get -Uri "http://localhost:5001/api/prediction/goats/A001/prediction?target_days=30" -Headers $headers -WebSession $s | ConvertTo-Json -Depth 4
```

## 5. 啟動 IoT 模擬器（選用）

```powershell
# 於前端建立 IoT 裝置後，取得一次性 API Key，再帶入以下指令
python .\iot_simulator\simulator.py --api-key <DEVICE_API_KEY> --device-type barn_environment --ingest-url http://localhost:5001/api/iot/ingest
```

## 6. 執行測試

### 後端

`backend/debug_test.py` 會讀取 `.env`，若設定 PostgreSQL 會連線資料庫。建議先暫存：

```powershell
cd backend
Rename-Item ..\..\.env ..\..\.env.bak
python -m pytest
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
Rename-Item ..\..\.env.bak ..\..\.env
```

覆蓋率 HTML 位於 `docs/backend/coverage/index.html`。

### 前端

```powershell
cd frontend
npm run test -- --run
npm run lint
npm run test:coverage -- --run
```

覆蓋率 HTML 位於 `docs/frontend/coverage/index.html`。

---

完成上述流程後，即可開始操作系統或繼續閱讀 [Development](./Development.md) 了解專案架構與開發實務。
