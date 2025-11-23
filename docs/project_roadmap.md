# 領頭羊博士開發工作藍圖

> 本文件紀錄 2025-10-05 討論後的開發任務、技術決策與實作指引，供日後開發者或 AI Agent 直接接續工作使用。

---

## A. 共通背景設定

- **部署現況**：後端 Flask 以 Session Cookie 驗證，前端 Vue 3；Docker Compose 版本含後端、前端、PostgreSQL。Ngrok 用於暫時公開前端與 API。
- **資料儲存**：主資料庫 PostgreSQL，測試環境可切換 SQLite。模型檔案放在 `backend/models/`。
- **AI 能力**：已整合 Gemini LLM。下一階段導入 Function Calling、RAG、指令化任務。
- **快取現況**：已改為 Redis（兼任輕量佇列 broker、Session store），Worker 可由 `backend/run_worker.py` 啟動。

---

## B. 工作主題與任務拆解

| 主題 | 描述 | 目標 | 下一步行動 | 依賴 / 注意事項 |
|------|------|------|-------------|------------------|
| **B1. 模型版本管理** | 為 LightGBM 等模型建立版本追蹤 | 模型可回滾、可比較 | 設計 `ModelRegistry` 資料表與儲存結構；調整訓練腳本寫入版本資訊 | 可先用檔案系統 + DB 紀錄，後續再評估 MLflow |
| **B2. IoT 資料接口** | 預留感測器資料流，先用模擬資料 | 成熟後可直接接 IoT 裝置 | 新增 `SensorReading` 模型與 `/api/sensors/ingest`；撰寫模擬器定時送資料 | API 需含 `device_id`、`sensor_type`、`value`、`recorded_at`；預留驗證欄位 |
| **B3. 時序特徵管線** | 將歷史或感測資料轉為 rolling feature | 提升健康/乳量等預測精度 | 建立 Feature 生成服務（讀 SensorReading → 寫 FeatureStore）；區分訓練與推論流程 | 生長模型維持原樣，避免與既有訓練資料不一致 |
| **B4. AI 助理 Function Calling** | 讓 Gemini 呼叫指定後端 API | 答覆採用即時資料 | 盤點可暴露的 API（例：`get_sheep_health_data`）；定義 function schema；調整後端代理層 | 需建立白名單與安全驗證；錯誤要有 fallback |
| **B5. AI 助理 RAG** | 導入 Gemini Embeddings 建知識庫 | 降低幻覺、提升專業性 | 規劃資料來源（SOP/FAQ/紀錄）；使用 `gemini-embedding-001` 產生向量；建向量庫 | 維度建議先 768；資料用 RETRIEVAL_DOCUMENT，查詢用 RETRIEVAL_QUERY；向量正規化 |
| **B6. Redis + 背景任務** | Redis 同時做快取、Broker、Session | 提升擴充性、支撐多實例 | ✅ 已完成：Docker Compose 加入 Redis、Session/快取改用 Redis、導入輕量佇列示範任務與 Worker | 後續可評估監控、重試與任務管理介面 |
| **B7. DB 索引優化** | 為高頻查詢欄位加 composite index | 改善查詢效能 | 透過 Alembic 新增索引，如 `SheepEvent(sheep_id, event_date)` 等 | 避免部署尖峰鎖表；上線前測試效能 |
| **B8. ESG 自動計算** | 根據操作記錄計算 ESG KPI | 自動產出 ESG 追蹤指標 | 定義計算公式；開發 `esg_service` 定期計算 `EsgSummary`；Dashboard 顯示結果 | 需可追溯數據來源；計算規則建置為可配置 |
| **B9. PWA 行動版** | 讓前端支援離線與手機操作 | 現場快速記錄 | 新增 manifest、service worker；調整 UI 流程（快速紀錄、照片上傳） | 需要處理 Session cookie 與離線時的資料同步策略 |
| **B10. 飼料成本分析** | 追蹤成本、存量、採購建議 | 協助節省成本 | 新增 `FeedPurchase/Inventory/Usage` 模型與管理 UI；AI 可引用資料產建議 | 支援資料匯入；需與報表/ESG 指標串接 |
| **B11. 健康預警 MVP** | 建立即時警報系統 | 提前偵測異常 | 設定簡易規則（溫度、高體重下降）；新增 `Alert` 模型/API；支援通知（Email/LINE） | 後續可改為 ML 模型；要有抑制重複警報的機制 |
| **B12. 繁殖/乳量管理** | 系統化管理繁殖與泌乳 | 改善生產計畫 | 新增 `BreedingRecord`, `LactationRecord`；建立提醒與統計圖表 | 與健康預警、飼料建議互通資訊 |
| **B13. 自動報表** | 定時產出政府或管理報表 | 減少人工整理 | 以 Celery 觸發背景任務產生 PDF/CSV；提供下載與 Email | 可使用 wkhtmltopdf/ReportLab；報表模組化 |
| **B14. 社群/知識共享 MVP** | 建立牧場交流空間 | 提升用戶黏著度 | 新增 `CommunityPost`, `Comment`；簡易審核機制 | 注意隱私與資料權限；先做內部實驗 |
| **B15. 產銷履歷 QR & Hash Chain** | 提供穩定 QR 與資料完整性證明 | 增強信任與公開透明 | 分享時要求使用者輸入最新 ngrok URL → 生成 QR；實作 hash chain（記錄批次資料 hash、prev_hash），定期將 root hash 上鏈做 timestamp | 後端需保存 hash trace；待正式域名後再改回固定 URL |
| **B16. Superset + ETL** | 導入開源 BI 平台 | 高階決策儀表板 | 部署 Apache Superset；使用 Celery 定期 ETL 到 `analytics` schema；建立預設 Dashboard | 需規劃 ETL 流程圖與同步策略；提供操作手冊 |

---

## C. AI 助理（RAG/Function Calling）詳細說明

### C1. 嵌入 (Embedding) 策略
- **模型**：`gemini-embedding-001`
- **維度建議**：開發階段使用 768；若需求提升可調整到 1536/3072。
- **批次產生**：優先使用 Batch API，一次處理多段落降低成本。
- **向量正規化**：生成後進行 L2 normalisation，計算餘弦相似度會更準確。
- **task_type**：文件用 `RETRIEVAL_DOCUMENT`，查詢用 `RETRIEVAL_QUERY`，可提升檢索精度。
- **資料來源**：牧場 SOP、疾病處置紀錄、飼料配方、常見問答、ESG 指南、產銷履歷流程。

### C2. RAG 推論流程
1. 使用者問題 → 轉成嵌入 → 向量庫比對 → 取相似段落。
2. Gemini 生成回答時，注入取回的段落（context）與需求指令。
3. 若需 Function Calling → LLM 判斷是否呼叫後端工具，取得即時資料後再生成答案。

### C3. 可用向量庫候選
- **開源自建**：ChromaDB、Qdrant
- **托管服務**：Pinecone、Weaviate 雲端版
- **資料庫擴充**：PostgreSQL + pgvector（若想減少新服務）

---

## D. QR 分享流程（Ngrok 暫行方案）

1. 使用者在後台點擊「生成公開連結」。
2. 系統提示輸入最新 ngrok URL（例：http://1234.ngrok.io）。
3. 後端組合公開批次頁面 URL（ngrok + `/trace/<batch_number>`）。
4. 產生 QR 圖檔（PNG/PDF）供下載或列印。
5. 記錄此次使用的 ngrok URL 以便追蹤。

> 若未來有固定域名，可將此手動步驟移除，改為自動生成固定 URL。

---

## E. 區塊鏈可行性 POC 策略

1. **Hash Chain**：每次修改批次資料計算 hash，並與前一筆 hash 串接。
2. **時間戳存證**：定期（例如每日）將最新 hash 上鏈（例：Ethereum、Polygon、Taiwan FIDO）。
3. **驗證機制**：使用者可下載批次資料與 hash，透過公開工具驗證是否遭竄改。
4. **後續評估**：若客戶需更高保障，再決定是否導入 Hyperledger 等私鏈。

---

## F. Superset + ETL 詳細流程

1. **ETL 管線**：
   - Celery beat 每日凌晨觸發任務。
   - 從主資料庫抽取 `Sheep`, `Events`, `ESG Summary`, `Feed Cost` 等資料。
   - 清洗、聚合後寫入 `analytics` schema；可使用 materialized views。

2. **Superset 部署**：
   - Docker 化佈署，連線至 analytics schema。
   - 建立預設儀表板：營運總覽、ESG 指標、健康警報、採購成本。
   - 提供登入方式（APP user 或 SSO）。

3. **整合建議**：在前端管理介面提供 Superset 入口，或嵌入特定 Dashboard iframe。

---

## G. 後續規劃建議

1. 建議依序完成 B1~B7 作為基礎體質，再進入 B9~B13 擴充使用者價值。
2. AI 深化（B4、B5、B11）可與 IoT/時序特徵並行規劃。
3. 市場加值（B14~B16）於核心功能穩定後執行，並搭配 POC 驗證效益。
4. 每個主題完成後更新本文件，補充新的決策或依賴。

---

## H. 資料資產與 Git LFS 策略

- **PDF / RAW 文件管理**：羊隻論文、SOP 等原始資料集中放在 `docs/rag_sources/`（或後續指定資料夾）。若為掃描件建議先壓縮或 OCR，降低容量、方便抽取文字。
- **向量結果保存**：Embedding 與 metadata 產出後寫入 `docs/rag_vectors/`（或專屬儲存庫）。建議存成 `.jsonl`、`.parquet` 或向量資料庫匯出檔，方便跨裝置復原而不必重跑。
- **Git LFS 可用額度**：GitHub 帳號目前每月享有 **10 GB 儲存 + 10 GB 頻寬** 的免費 LFS 使用量。若預估 1~2 GB 即可滿足需求，仍在免費額度內；超額時可購買 Data Pack（50 GB / 5 USD / 月）。
- **容量估算參考**：768 維向量約 3 KB/段，10,000 段約 30 MB；PDF 純文字 50~100 KB/頁，1 GB 可放 10,000–20,000 頁。依此規劃資料批次與清理策略。
- **憑證與授權**：Git LFS 沿用 Git 認證（PAT、SSH 或帳密），無需額外金鑰。自動化流程請透過環境變數或秘密管理服務提供 PAT，避免把敏感資訊寫死在程式碼。
- **多環境部署**：若改在其他機器部署，只要拉取向量檔或向量庫快照即可。若要使用雲端向量服務（Pinecone/Qdrant Cloud），將 API key 交由環境變數管理，避免重複執行嵌入。
- **版本控管與紀錄**：每次新增或更新資料，請在此文件或專屬 CHANGELOG 註明「PDF/向量來源、生成日期、使用嵌入模型與維度」，確保團隊與 AI Agent 能追溯資料來源。

### H1. Git LFS 操作流程

1. **放置檔案**：將原始 PDF 或掃描檔放在 `docs/rag_sources/`，嵌入向量匯出檔放在 `docs/rag_vectors/` 或其它規畫好的資料夾。
2. **初始化 LFS（專案首次執行）**：`git lfs install`
3. **設定追蹤規則**：以 `git lfs track "docs/rag_sources/*.pdf"`、`git lfs track "docs/rag_vectors/*"` 更新 `.gitattributes`，必要時加入大小寫或其他副檔名。
4. **提交追蹤設定**：`git add .gitattributes` → `git commit -m "Configure Git LFS for RAG assets"`。
5. **提交實際檔案**：`git add docs/rag_sources/ docs/rag_vectors/` → 撰寫適當的 commit message → `git push`。
6. **驗證結果**：執行 `git lfs ls-files` 確認檔案已被 LFS 管理。

> 若先前已以一般 Git 提交大型檔案，可使用 `git lfs migrate import --include="docs/rag_sources/*,docs/rag_vectors/*"` 重新寫入歷史，或重新建立提交，避免 repo 保留巨量 blobs。

---

**維護人員備註**：如需了解現有架構與 API，請參閱 `docs/README.md`、`docs/Development.md`、`backend/docs/README.md`、`frontend/docs/README.md`。若有新討論，請在此文件補充決策與工作項目狀態。
