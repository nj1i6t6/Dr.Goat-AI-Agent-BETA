# API 索引

- Swagger UI：<http://localhost:5001/docs>
- OpenAPI 規格：<http://localhost:5001/openapi.yaml>
- 所有 `/api/*` 端點預設回傳 JSON，除 `export_excel` 為二進位檔案。
- 除 `/api/auth/*`（部分）與 `/api/traceability/public/*` 外，其餘端點皆需登入並攜帶 Session Cookie。

## 認證模組 `/api/auth`

| Method | Path | 說明 | 備註 |
|--------|------|------|------|
| POST | `/register` | 建立新帳號並自動登入 | 首次註冊會建立預設事件選項 |
| POST | `/login` | 使用者登入 | 驗證失敗回傳 401 |
| POST | `/logout` | 登出目前登入者 | 需登入 |
| GET | `/status` | 回傳登入狀態與帳號資訊 | 可作健康檢查 |
| GET | `/health` | 健康檢查 | Docker liveness probe |

## 羊隻管理 `/api/sheep`

| Method | Path | 說明 |
|--------|------|------|
| GET | `/` | 列出當前使用者所有羊隻（依耳號排序） |
| POST | `/` | 新增羊隻，使用 Pydantic `SheepCreateModel` 驗證 |
| GET | `/{ear_num}` | 取得單一羊隻所有欄位與事件列表 |
| PUT | `/{ear_num}` | 更新羊隻資料，會自動記錄體重/產奶歷史 |
| DELETE | `/{ear_num}` | 刪除羊隻（連帶刪除事件與歷史） |
| GET | `/{ear_num}/events` | 取得羊隻事件列表（依時間 DESC） |
| POST | `/{ear_num}/events` | 新增事件，驗證 `SheepEventCreateModel` |
| PUT | `/events/{event_id}` | 更新事件內容 |
| DELETE | `/events/{event_id}` | 刪除事件 |
| GET | `/{ear_num}/history` | 取得歷史數據（體重/奶量/乳脂等） |
| DELETE | `/history/{record_id}` | 刪除單筆歷史記錄 |

## 資料管理 `/api/data`

| Method | Path | 說明 | 注意事項 |
|--------|------|------|----------|
| GET | `/export_excel` | 匯出羊隻、事件、歷史、聊天紀錄 | 回傳 `xlsx`，空資料時會提供說明工作表 |
| POST | `/analyze_excel` | 分析上傳 Excel 結構並回傳欄位預覽 | `multipart/form-data`，檔案欄位為 `file` |
| POST | `/ai_import_mapping` | 使用 Gemini 分析工作表用途與欄位映射 | 需提供 `file`；優先使用 header `X-Api-Key`，否則 fallback `GOOGLE_API_KEY` |
| POST | `/process_import` | 導入 Excel | `is_default_mode=true` 使用內建映射；手動模式需附 `mapping_config` JSON |

## 儀表板 `/api/dashboard`

| Method | Path | 說明 |
|--------|------|------|
| GET | `/data` | 聚合提醒、停藥、健康警示、ESG 指標；含 Redis 90 秒快取 |
| GET | `/farm_report` | 產生牧場統計報告（品種、性別、疾病統計） |
| GET | `/event_options` | 取得自訂與預設事件類型（含描述） |
| POST | `/event_types` | 新增事件類型 |
| DELETE | `/event_types/{type_id}` | 刪除事件類型（不可刪預設項） |
| POST | `/event_descriptions` | 新增事件描述 |
| DELETE | `/event_descriptions/{desc_id}` | 刪除事件描述 |

## AI 代理 `/api/agent`

> 所有端點需在標頭帶入 `X-Api-Key: <Google Gemini API Key>`，若未提供且伺服器未設定 `GOOGLE_API_KEY` 會回傳 401。

| Method | Path | 說明 |
|--------|------|------|
| GET | `/tip` | 根據季節產出每日飼養小提示（Markdown 轉 HTML） |
| POST | `/recommendation` | 產生營養建議、ESG 分析與餵飼指引 | 需於標頭提供 X-Api-Key 以及羊隻資訊；會自動補入資料庫背景 |
| POST | `/chat` | 與 AI 對話；支援純 JSON 或 `multipart/form-data` 圖片上傳 | `image` 欄位支援 JPEG/PNG/GIF/WebP，最大 10 MB |

## 生長預測 `/api/prediction`

> 需登入且必須提供 `X-Api-Key`。

| Method | Path | 說明 |
|--------|------|------|
| GET | `/goats/{ear_tag}/prediction?target_days=30` | 以歷史體重做 LightGBM/線性迴歸預測，回傳平均日增重、信賴區間、數據品質報告與 LLM 說明 |
| GET | `/goats/{ear_tag}/prediction/chart-data?target_days=30` | 取得圖表所需的歷史點、趨勢線、預測點與信賴區間 |

## 產品產銷履歷 `/api/traceability`

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/batches?include_details=true` | 列出登入使用者的批次；可選擇載入加工步驟與羊隻關聯 | 需登入 |
| POST | `/batches` | 建立批次，可一次性附帶加工步驟與羊隻關聯 | 需登入 |
| GET | `/batches/{batch_id}` | 取得單一批次詳細資料 | 需登入 |
| PUT | `/batches/{batch_id}` | 更新批次資訊與公開狀態 | 需登入 |
| DELETE | `/batches/{batch_id}` | 刪除批次及其加工步驟、羊隻關聯 | 需登入 |
| POST | `/batches/{batch_id}/steps` | 新增加工步驟 | 需登入 |
| PUT | `/steps/{step_id}` | 更新加工步驟內容 | 需登入 |
| DELETE | `/steps/{step_id}` | 刪除加工步驟 | 需登入 |
| POST | `/batches/{batch_id}/sheep` | 以陣列替換羊隻關聯（會刪除舊資料） | 需登入 |
| DELETE | `/batches/{batch_id}/sheep/{sheep_id}` | 移除單筆羊隻關聯 | 需登入 |
| GET | `/public/{batch_number}` | 不需登入即可取得公開批次故事、加工流程時間軸、羊隻摘要 | 公開 |

## IoT 自動化 `/api/iot`

| Method | Path | 說明 | 備註 |
|--------|------|------|------|
| GET | `/devices` | 列出登入使用者的裝置 | 需登入 |
| POST | `/devices` | 建立裝置並產生一次性 API Key | 回傳 `api_key` 只顯示一次，請妥善保存 |
| GET | `/devices/{device_id}` | 取得裝置詳細資訊 | 需登入 |
| PUT | `/devices/{device_id}` | 更新裝置資料 | 不可透過此端點更新 API Key |
| DELETE | `/devices/{device_id}` | 刪除裝置與相關資料 | 需登入 |
| GET | `/devices/{device_id}/readings?limit=100` | 取得最近感測讀值 | 需登入，最多 500 筆 |
| POST | `/ingest` | 感測資料上報 | 需於 Header 帶 `X-API-Key`（大小寫皆可）；驗證後寫入佇列 |
| GET | `/rules` | 列出自動化規則 | 需登入 |
| POST | `/rules` | 建立規則 | 需登入；觸發裝置必須為感測器、目標裝置必須為致動器 |
| PUT | `/rules/{rule_id}` | 更新規則 | 需登入 |
| DELETE | `/rules/{rule_id}` | 刪除規則 | 需登入 |

## 背景任務 `/api/tasks`

| Method | Path | 說明 | 備註 |
|--------|------|------|------|
| POST | `/example` | 建立示範性的儀表板快照任務並排入 `SimpleQueue` | 需登入；回傳 `job_id` 可供 Worker 追蹤 |

## 通用規則

- **錯誤格式**：失敗時回傳 `{ "error": "..." }`，必要時包含 `details` 或 `field_errors`。HTTP 狀態碼對應錯誤類型。
- **日期格式**：統一採 `YYYY-MM-DD`；Excel 匯入會自動排除 `1900-01-01` 等空值標記。
- **授權**：所有資料依 `current_user.id` 隔離，無跨使用者操作。IoT API Key 使用 HMAC 與常數時間比較驗證。
- **快取**：儀表板資料以 Redis `setex` 儲存；若需強制更新可呼叫後端 `clear_dashboard_cache` 或等待 TTL。
- **背景任務**：`SimpleQueue` 使用 Redis list；Worker 需啟動 `python backend/run_worker.py` 處理排隊工作與 IoT 控制佇列。

完整欄位與範例請參閱 Swagger UI 或 `backend/openapi.yaml`。
