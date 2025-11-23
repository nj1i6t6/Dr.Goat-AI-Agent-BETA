# 常見問題（FAQ）

## 登入 API 回傳 401？
- 先呼叫 `POST /api/auth/register` 建立帳號（會自動登入）。
- 若已登入仍收到 401，請確認瀏覽器允許 Cookie，或 API 客戶端是否攜帶 Session Cookie。
- 若從前端收到自動登出，代表 session 逾時或 Redis 連線失敗，請檢查 `backend` 日誌。

## 後端測試嘗試連線 PostgreSQL 導致失敗？
- `backend/debug_test.py` 會在模組載入時讀取 `.env`。執行測試前請暫時將 `.env` 改名，或設定 `$env:DOTENV_PATH="NON_EXISTENT_.env"` 後再執行 `pytest`。
- 測試會自動使用 SQLite 與 InMemory Redis，不需額外啟動資料庫。

## AI 相關端點（/api/agent、/api/prediction）回傳缺少 API 金鑰？
- 請在請求標頭加入 `X-Api-Key: <你的 Google Gemini API Key>`。
- 或於 `.env` / Docker Compose 設定 `GOOGLE_API_KEY`，前端會自動帶入該值。
- 若仍失敗，檢查是否超過 Gemini 配額或網路防火牆阻擋外部請求。

## 匯入 Excel 失敗？
- 確認檔案為 `.xlsx` / `.xls`，且未被密碼保護。
- 日期欄位建議為 `YYYY-MM-DD`，1900/1/1 或包含 1900 的值會被視為空值。
- 自訂映射模式需提供 `mapping_config` JSON 並於 `FormData` 中傳遞；AI 映射回傳的 `warnings` 需人工確認後再匯入。

## IoT 裝置無法上傳資料？
- 建立裝置後出現的一次性 `api_key` 必須立即儲存；若遺失請刪除裝置重新建立。
- 上報時需在標頭使用 `X-API-Key`（大小寫不限），且 `API_HMAC_SECRET` 需與伺服器一致。
- 檢查 Redis 是否可用，若 `iot:sensor_queue` 未增加資料代表上報失敗。

## 自動化規則沒有被觸發？
- 確認觸發裝置類型為 `sensor`、目標裝置為 `actuator`。
- 於資料庫 `SensorReading` 查詢最新值，確認欄位名稱與規則條件一致。
- 檢查 Worker 日誌是否出現 `Evaluating rule` 或 `Processing control payload` 訊息，必要時重新啟動 `run_worker.py`。

## 如何查看最新測試覆蓋率？
- 後端：`docs/backend/coverage/index.html`
- 前端：`docs/frontend/coverage/index.html`
- 若 HTML 尚未更新，請依 [QuickStart](./QuickStart.md) 中指令重新產生。

## Docker 啟動後前端顯示空白？
- 確認前端容器的 Nginx 已啟動：`docker compose logs frontend`。
- 檢查 `.env` 是否設定 `CORS_ORIGINS`，至少包含 `http://localhost:3000`。
- 如使用自訂網域，請同步更新前端環境變數並重新 build。

## 端口衝突？
- 預設埠號：前端 3000（容器對外 80）、後端 5001、PostgreSQL 5432、Redis 6379。
- 若本地已有服務占用，可調整 `docker-compose.yml` 或 `.env` 對應埠口後重建。

## 可以不依賴 Docker 嗎？
- 可以，請依 [Development](./Development.md) 啟動 Flask 與 Vite。
- 本機測試預設使用 SQLite + InMemory Redis，若需 PostgreSQL 請自行啟動資料庫並更新 `.env`。

## Redis 連不上或快取失效？
- 確認本機或 Docker `redis` 服務已啟動，且密碼與 `.env` 中 `REDIS_PASSWORD` 一致。
- 可使用 `redis-cli -a <密碼> ping` 測試；開發環境可設定 `USE_FAKE_REDIS_FOR_TESTS=1` 改用記憶體實作。

## 背景任務沒有執行？
- `/api/tasks/example` 回傳的 `job_id` 需要由背景 Worker 處理，請啟動 `python run_worker.py` 或部署對應服務。
- 若佇列卡住，可在 Redis 內查看 `simple-queue:*` 或 `iot:control_queue` 是否累積資料，必要時重啟 Worker。

## 產品產銷履歷公開頁會洩漏資料嗎？
- 公開 API `/api/traceability/public/<批次號>` 只回傳必要欄位，移除使用者 ID 與內部識別碼。
- 建議批次號採不可預測字串，並於反向代理設定速率限制。

## 何處可以找到系統架構示意圖？
- 所有圖片集中在 `docs/assets/`，例如部署架構 `docs/assets/deployment.png`。
- 如需更新，請同步於 README 與 `docs/README.en.md` 引用。
