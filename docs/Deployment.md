# 部署指南

> 建議使用 Docker Compose，一次啟動前端 Nginx、Flask 後端、PostgreSQL、Redis 與可選的 IoT 模擬器。

![部署架構示意](./assets/deployment.png)

## 事前準備

| 項目 | 建議版本 |
|------|----------|
| Docker Desktop / Engine | 24.x 以上 |
| Docker Compose | v2 |
| 伺服器資源 | 至少 2 vCPU / 4 GB RAM |

## 1. 設定環境變數

```powershell
Copy-Item .env.example .env
notepad .env
```

請務必填寫以下關鍵參數：

| 變數 | 說明 |
|------|------|
| `SECRET_KEY` | Flask Session 密鑰（建議使用 `python -c "import secrets; print(secrets.token_hex(32))"` 產生）。 |
| `API_HMAC_SECRET` | IoT API Key HMAC 密鑰，至少 32 bytes，修改後需重新建立裝置。 |
| `POSTGRES_*` | 資料庫帳號/密碼/主機/埠口/資料庫名。 |
| `REDIS_PASSWORD` | Redis 密碼，需與 `docker-compose.yml` 內一致。 |
| `CORS_ORIGINS` | 生產環境允許的前端來源清單（逗號分隔）。 |
| `GOOGLE_API_KEY` | Google Gemini API 金鑰（若前端未帶 `X-Api-Key` 時使用）。 |
| `RQ_QUEUE_NAME` | 背景任務佇列名稱（預設 `default`）。 |

## 2. 佈署與檢查

```powershell
docker compose up --build -d
docker compose ps
```

啟動後建議驗證：

| 項目 | URL / 指令 | 正常回應 |
|------|-------------|-----------|
| 前端 | http://localhost:3000 | Vue SPA 首頁 |
| 後端健康檢查 | http://localhost:5001/api/auth/status | `{ "logged_in": false }` |
| Swagger | http://localhost:5001/docs | Swagger UI 頁面 |
| IoT Ingest | `curl -I http://localhost:5001/api/iot/ingest` | 401（未帶 API key 屬正常） |
| PostgreSQL | `docker compose logs db` | `database system is ready to accept connections` |
| Redis | `docker compose logs redis` | `Ready to accept connections` |
| Worker | `docker compose logs backend` | 出現 `Loaded .env`、`Redis connection established`、`SimpleQueue` 初始化訊息 |

## 3. 資料庫遷移

容器啟動時會執行 `flask db upgrade`。若需手動遷移或補救：

```powershell
docker compose exec backend flask db upgrade
```

首次自 SQLite 遷移至 PostgreSQL，可先在本機匯出 SQLite，再透過 `psql` 匯入資料庫。

## 4. 常見維運命令

```powershell
# 查看服務日誌
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f redis

# 重啟單一服務
docker compose restart backend

docker compose restart iot_simulator  # 重新產生模擬資料

# 套用新映像後背景更新
docker compose up --build -d

# 停止並移除容器、網路、匿名 volume
docker compose down
```

## 5. 版本更新流程

1. 更新程式碼（`git pull` 或 CI/CD 發布）。
2. 同步 `.env`、`docker-compose.yml` 或額外設定檔。
3. `docker compose up --build -d` 重建映像與容器。
4. `docker compose exec backend flask db upgrade` 確認資料庫結構最新。
5. 造訪 `/api/auth/status` 與前端頁面確認服務可用，必要時檢查 worker 與 IoT 模擬器日誌。

## 6. 備份與還原

```powershell
# PostgreSQL 備份（主機端執行）
docker compose exec db pg_dump -U $env:POSTGRES_USER $env:POSTGRES_DB > backup.sql

# PostgreSQL 還原
type backup.sql | docker compose exec -T db psql -U $env:POSTGRES_USER $env:POSTGRES_DB

# 匯出後端日誌或模型資產
docker compose cp backend:/app/logs ./logs-backup
docker compose cp backend:/app/models ./models-backup
```

如需備份上傳檔案，可額外掛載 volume（`backend/uploads`）。

## 7. IoT 模擬器設定

`docker-compose.yml` 內 `iot_simulator` 服務預設使用環境變數：

- `API_KEY`：需對應前端建立裝置後顯示的一次性金鑰。
- `INGEST_URL`：預設 `http://backend:5001/api/iot/ingest`。
- `DEVICE_TYPE`：支援 `barn_environment`、`wearable_tag` 等類型。
- `SEND_INTERVAL_SECONDS`：資料推送頻率。

可複製該服務區塊建立多個模擬器，記得更新 `container_name` 與 `API_KEY`。

## 8. 佈署後檢查清單

- [ ] `/api/auth/status` 回傳 200 且 Cookie 正常寫入。
- [ ] `/api/data/export_excel` 能匯出檔案。
- [ ] `/api/traceability/batches`、`/api/traceability/public/<批次號>` 依權限回傳正確資料。
- [ ] `/api/agent/tip`、`/api/prediction/goats/<ear>/prediction` 於提供 API Key 後回傳預期內容。
- [ ] Redis 連線正常、`dashboard-cache:*` 可寫入且 TTL 運作正常。
- [ ] 背景 Worker 有持續輸出 `Processing control payload` 等日誌。
- [ ] IoT 模擬器每隔指定秒數產生讀值並觸發自動化規則（可查看 `SensorReading` 與 `DeviceControlLog` 資料表）。
- [ ] 覆蓋率報告（`docs/backend/coverage/index.html`、`docs/frontend/coverage/index.html`）已備份或上傳供稽核使用。

完成上述流程後即可交付或布建監控。更多開發建議請參閱 [Development](./Development.md)。
