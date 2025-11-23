# 開發指南

## 推薦環境

| 範疇 | 推薦版本 |
|------|-----------|
| Python | 3.11.x |
| Node.js | 20.x |
| npm | 10.x |
| PostgreSQL（選用） | 14+ |
| Redis | 7.2+ |

> `.env.example` 僅示意部分變數，實際開發請補齊 `SECRET_KEY`、`API_HMAC_SECRET`、`GOOGLE_API_KEY` 等必填欄位。

## 後端開發流程

1. 建立虛擬環境與安裝套件：
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. 啟動 Flask：
   ```powershell
   $env:REDIS_PASSWORD = "<REDIS_PASSWORD>"
   $env:FLASK_ENV = "development"
   $env:CORS_ORIGINS = "http://localhost:5173"
   python run.py
   ```
3. 預設使用 SQLite (`instance/app.db`)；若 `.env` 內設定 `POSTGRES_*`，啟動時會切換 PostgreSQL，並在首次啟動呼叫 `db.create_all()`。
4. Redis 連線預設取自 `REDIS_URL` 或 `REDIS_HOST/PORT/PASSWORD`；測試環境可設 `USE_FAKE_REDIS_FOR_TESTS=1` 使用記憶體版模擬器。
5. Swagger UI 位於 `http://localhost:5001/docs`，`/openapi.yaml` 可匯入 Postman/Insomnia。
6. 儀表板資料透過 `app/cache.py` 快取 90 秒，寫入羊隻/事件/歷史後會呼叫 `clear_dashboard_cache(user_id)` 自動失效。

### 重要模組速覽

| 模組 | 說明 |
|------|------|
| `app/api/auth.py` | 註冊/登入、預設事件類型與健康檢查。 |
| `app/api/sheep.py` | 羊隻 CRUD、事件、歷史紀錄、自動記錄體重/奶量變動。 |
| `app/api/dashboard.py` | 提醒、停藥期、健康警示、事件詞庫管理、Redis 快取。 |
| `app/api/data_management.py` | Excel 匯出、AI 映射、匯入流程與錯誤報告。 |
| `app/api/agent.py` | Gemini 每日提示、營養/ESG 建議、多模態聊天。 |
| `app/api/prediction.py` | LightGBM/線性回歸預測、資料品質檢查、ESG 解讀。 |
| `app/api/traceability.py` | 產品批次、加工步驟、羊隻關聯與公開故事。 |
| `app/api/iot.py` | 裝置管理、API Key HMAC、感測資料攝取、自動化規則。 |
| `app/api/tasks.py` + `app/tasks.py` | `SimpleQueue` 背景任務示範與佇列包裝。 |
| `app/iot/automation.py` | 感測/控制佇列、規則判斷、HTTP 控制派送與紀錄。 |
| `app/utils.py` | Gemini 呼叫、羊隻上下文聚合、圖片編碼。 |

### IoT 自動化工作流程

1. 前端透過 `/api/iot/devices` 建立裝置並取得一次性 API Key。
2. 感測器呼叫 `/api/iot/ingest`，驗證 HMAC API Key 後寫入 `SensorReading` 並推送 Redis 佇列。
3. `process_sensor_payload` 讀取佇列，比對 `AutomationRule.trigger_condition`，符合條件即推送控制佇列。
4. `process_control_command` 依裝置 `control_url` 發送 HTTP 指令並寫入 `DeviceControlLog`。
5. Worker (`run_worker.py`) 會同時處理背景任務佇列與 IoT 控制佇列。

## 前端開發流程

1. 安裝依賴並啟動 Vite：
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
2. 開發伺服器 `http://localhost:5173` 透過 `vite.config.js` 代理 `/api` 至 `http://127.0.0.1:5001`。
3. 所有受保護路由掛載在 `AppLayout.vue` 下，透過路由守衛與 `stores/auth.js` 的 `isAuthenticated` 控制。
4. API 呼叫統一使用 `src/api/index.js`，可傳入 error handler 取得 `handleApiError` 已格式化的訊息。
5. Pinia store 位於 `src/stores/`，每個 store 皆附自動化測試（`*.test.js`），並善用 composable 例如 `useConsultationStore` 整合 API、UI 狀態與錯誤處理。
6. 元件單元測試與行為測試放在同層 `*.test.js` / `*.behavior.test.js`，使用 Element Plus 提供的測試 ID。

### 主要路由與頁面

| 路由 | 視圖 | 重點功能 |
|------|------|----------|
| `/dashboard` | `DashboardView.vue` | 儀表板提醒、健康警示、ESG 指標圖表。 |
| `/consultation` | `ConsultationView.vue` | 填寫羊隻狀態，呼叫 `/api/agent/recommendation` 顯示 Markdown 回覆。 |
| `/chat` | `ChatView.vue` | 多模態聊天、歷史紀錄、圖片上傳與預覽。 |
| `/flock` | `SheepListView.vue` | 羊隻列表、詳細抽屜、事件/歷史 CRUD。 |
| `/data-management` | `DataManagementView.vue` | 匯出、匯入、AI 欄位映射、導入報告。 |
| `/prediction` | `PredictionView.vue` | 生長預測圖表、AI 說明、品質報告。 |
| `/iot` | `IotManagementView.vue` | 裝置與規則管理、即時讀值。 |
| `/traceability` | `TraceabilityManagementView.vue` | 批次/加工步驟/羊隻關聯維護，QR code 分享。 |
| `/settings` | `SettingsView.vue` | Gemini API Key 儲存、背景任務觸發。 |
| `/trace/:batchNumber` | `TraceabilityPublicView.vue` | 公開批次故事頁，無需登入。 |

## 測試與覆蓋率

### 後端

- 執行測試：
  ```powershell
  cd backend
  Rename-Item ..\..\.env ..\..\.env.bak
  python -m pytest
  python -m pytest --cov=app --cov-report=term-missing --cov-report=html
  Rename-Item ..\..\.env.bak ..\..\.env
  ```
- `backend/tests/conftest.py` 會：
  - 清除 `POSTGRES_*`，強制使用 SQLite in-memory。
  - 將 `USE_FAKE_REDIS_FOR_TESTS` 設為 1，掛載 `InMemoryRedis`。
  - 建立測試使用者與 `authenticated_client` fixture。
  - 模擬 Gemini API 回傳內容以避免外部依賴。
- HTML 覆蓋率輸出於 `docs/backend/coverage/index.html`。

### 前端

- 執行測試：
  ```powershell
  cd frontend
  npm run test -- --run
  npm run lint
  npm run test:coverage -- --run
  ```
- 行為測試（例如 `ConsultationView.behavior.test.js`）會模擬 API 回應並檢查 UI 互動。
- 覆蓋率報告位於 `docs/frontend/coverage/index.html`。

## 常用指令速查

```powershell
# 產生與套用資料庫遷移
flask db migrate -m "描述"
flask db upgrade

# 指定測試
pytest tests/test_prediction_api.py::TestPredictionAPI::test_get_sheep_prediction

# 啟動背景任務 Worker（處理 SimpleQueue 與 IoT 控制佇列）
python run_worker.py

# 建立測試資料
python create_test_data.py

# 分析前端 bundle
npm run build -- --analyze
```

## 日誌與除錯

- 後端預設輸出至 STDOUT，可依需求於 `FLASK_ENV=production` 搭配 `gunicorn` 或 Nginx 轉存檔案。
- 手動測試腳本：`manual_test.py`、`manual_functional_test.py`、`test_full_api.py` 可快速驗證端到端流程。
- IoT 佇列除錯：使用 `redis-cli -a <PASSWORD> LRANGE iot:sensor_queue 0 -1` 觀察排隊資料。
- 前端建議安裝 Vue DevTools 與 Pinia DevTools；Vitest 失敗時可使用 `npm run test -- <pattern>` 定位問題。

## 開發建議

- AI 相關端點需有效 `GOOGLE_API_KEY` 或前端手動帶入 `X-Api-Key`；若回傳缺少金鑰訊息，請確認環境變數是否設定。
- 調整 `API_HMAC_SECRET` 時需重新建立 IoT 裝置以取得新的 API Key。舊金鑰會失效。
- 匯入流程若需新增欄位，請同步更新 `REQUIRED_COLUMNS_BY_PURPOSE` 與 Pydantic Schema，並補充測試案例。
- 前端新增 API 時，務必在 `src/api/index.js` 集中管理並補齊 Pinia store 測試。
- 文件為英/中對照，新增功能時請先更新 `docs/README.en.md`、再同步 README.md 並補充 `docs/glossary.md` 術語。
