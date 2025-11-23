# 領頭羊博士 - 後端 API 服務

> 🐐 基於 Flask + SQLAlchemy 的山羊營養管理系統後端服務

## 📋 系統概述

本後端服務採用 Flask 3.0.3 框架，提供完整的 RESTful API，整合 Google Gemini AI 技術，為山羊營養管理系統提供核心業務邏輯支援。

## ⚠️ 模型適用範圍

- LightGBM 成長模型主要以出生一年內（≤365 天）的幼年羊隻資料訓練，超出範圍時仍會提供預測但需審慎解讀。
- API 僅檢查「目前日齡」是否 ≤365 天；若符合，預測區間可以延伸至一年以外。
- 若羊隻缺少出生日期，也會被要求補齊後才能進行預測。

## 📈 預測輸出結構

- `daily_forecasts`：從今日開始到目標天數（含）為止的逐日體重預估，提供圖表繪製與資料導出使用。
- `daily_confidence_band`：若量化（q10/q90）模型可用，會同步提供每日信賴區間上下界；若模型備援為線性迴歸，則此欄位為空。
- `/prediction/chart-data` 端點會回傳對應的 `forecast_line` 與 `confidence_band`，前端以單一趨勢線搭配信賴區間界線呈現。

## 🏗️ 技術架構

### 核心技術棧
- **Web 框架**：Flask 3.0.3
- **ORM**：SQLAlchemy 2.0.31
- **資料驗證**：Pydantic 2.7.1 (V1→V2 完整遷移)
- **資料庫遷移**：Alembic 1.13.1
- **AI 整合**：Google Generative AI 0.8.5
- **身份驗證**：Flask-Login 0.6.3
- **Session / 快取**：Flask-Session 0.5.0 + Redis 5（Session、儀表板快取）
- **背景任務**：輕量 RQ 風格佇列（Redis Broker）
- **測試框架**：pytest 8.2.0 + pytest-cov 5.0.0
- **WSGI 伺服器**：Waitress 3.0.0
- **Excel 處理**：openpyxl 3.1.4 + pandas 2.2.2

### 專案結構
```
backend/
├── app/                        # Flask 應用程式核心
│   ├── __init__.py             # Flask 應用程式工廠
│   ├── cache.py                # Redis 儀表板快取
│   ├── error_handlers.py       # 統一錯誤處理器
│   ├── models.py               # SQLAlchemy 資料模型
│   ├── schemas.py              # Pydantic 資料驗證模型
│   ├── tasks.py                # 輕量 RQ 風格背景任務與佇列工具
│   ├── utils.py                # 工具函數與 AI 整合
│   └── api/                    # RESTful API 藍圖
│       ├── __init__.py         # API 藍圖註冊
│       ├── agent.py            # AI 代理人 API
│       ├── auth.py             # 身份驗證 API
│       ├── dashboard.py        # 儀表板數據 API
│       ├── data_management.py  # 數據管理 API
│       ├── prediction.py       # 生長預測 API
│       ├── tasks.py            # 背景任務觸發 API
│       ├── traceability.py     # 產品產銷履歷 API（批次、加工流程、公開端）
│       └── sheep.py            # 山羊管理 API
├── instance/                   # Flask 實例特定檔案
│   └── app.db                  # SQLite 開發資料庫
├── migrations/                 # Alembic 資料庫遷移
│   ├── env.py                  # 遷移環境配置
│   ├── script.py.mako          # 遷移腳本範本
│   └── versions/               # 資料庫版本控制
│       └── 20240723_add_core_indexes.py    # 核心複合索引遷移
└── tests/                      # 測試套件（Pytest）
    ├── conftest.py             # pytest 測試配置與夾具
    ├── test_agent_api.py       # AI 代理人 API 測試 (18 tests)
    ├── test_auth_api.py        # 身份驗證 API 測試 (10 tests)
    ├── test_dashboard_api.py   # 儀表板 API 測試 (11 tests)
    ├── test_data_management_api.py # 數據管理 API 測試 (12 tests)
    ├── test_traceability_api.py    # 產品批次與公開履歷流程測試
    ├── test_tasks_api.py       # 背景任務與 API 測試
    ├── test_sheep_api.py       # 山羊管理 API 測試 (13 tests)
    ├── test_*_enhanced.py      # 增強測試套件 (130+ tests)
    ├── test_*_error_handling.py # 錯誤處理測試
    └── test_*_events_api.py    # 事件管理測試
```

## 🚀 快速開始

### 環境需求
- Python 3.11+
- PostgreSQL 13+ (生產環境) / SQLite (開發環境)
- Redis 5+（快取、Session 與背景任務佇列）

### 安裝步驟

1. **建立虛擬環境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

2. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
複製並編輯環境變數檔案：
```bash
cp .env.example .env
```
確保 `.env` 或系統環境變數中設定 `REDIS_PASSWORD`（請參考 `.env.example`）與 `REDIS_HOST`（本機開發可為 `localhost`）。

4. **初始化資料庫**
```bash
flask db upgrade
```

5. **啟動開發伺服器**
```bash
export REDIS_PASSWORD=<REDIS_PASSWORD>  # Windows 請使用 set / $env 並參考 .env.example
python run.py
```

## 📊 API 端點總覽

### 身份驗證 API (/api/auth)
- `POST /login` - 用戶登入
- `POST /register` - 用戶註冊  
- `GET /status` - 檢查登入狀態
- `POST /logout` - 用戶登出

### 山羊管理 API (/api/sheep)
- `GET /` - 取得山羊列表
- `POST /` - 新增山羊記錄
- `GET /<id>` - 取得單一山羊資料
- `PUT /<id>` - 更新山羊資料
- `DELETE /<id>` - 刪除山羊記錄

### AI 代理人 API (/api/agent)
- `GET /tip` - 每日小貼士
- `POST /recommendation` - 輸出營養/ESG 建議
- `POST /chat` - AI 對話諮詢（支援圖片上傳）

### 儀表板 API (/api/dashboard)
- `GET /data` - 聚合統計與提醒（含快取）
- `GET /farm-report` - 生成牧場報告
- `GET /event_options` - 事件類型/描述管理

### 數據管理 API (/api/data)
- `GET /export_excel` - 匯出 Excel 檔案
- `POST /analyze_excel` - 分析檔案格式
- `POST /process_import` - 匯入 Excel 資料

### 生長預測 API (/api/prediction)
- `GET /goats/<ear_tag>/prediction` - 生長趨勢預測
- `GET /goats/<ear_tag>/prediction/chart-data` - 趨勢圖與信賴區間資料

### 背景任務 API (/api/tasks)
- `POST /example` - 建立示範性的儀表板快照任務（使用 Redis + 輕量佇列）

### 產品產銷履歷 API (/api/traceability)
- `GET /batches` - 列出登入者批次（可含加工步驟/羊隻關聯）
- `POST /batches` - 建立批次與初始步驟/羊隻
- `PUT /batches/<id>` / `DELETE /batches/<id>` - 維護批次
- `POST /batches/<id>/steps`、`PUT /steps/<step_id>`、`DELETE /steps/<step_id>` - 管理加工流程
- `POST /batches/<id>/sheep`、`DELETE /batches/<id>/sheep/<sheep_id>` - 維護羊隻關聯
- `GET /public/<batch_number>` - 取得公開履歷故事（無需登入）

## 🧪 測試覆蓋率

### 測試概況
- Pytest 覆蓋 Auth、Sheep、Data Management、Dashboard、Agent、Prediction 與 Traceability 模組。
- 產銷履歷測試 (`tests/test_traceability_api.py`) 驗證批次 CRUD、步驟與羊隻關聯、公開端口權限。
- HTML 覆蓋率報告產出於 `../docs/backend/coverage/index.html`，建議持續補強 `app/api/dashboard.py`。

### 執行測試
```bash
# 執行所有測試
pytest

# 執行測試並產生覆蓋率報告
pytest --cov=app --cov-report=html

# 執行特定測試檔案
pytest tests/test_sheep_api.py -v
```

## 🔧 開發工具

### 資料庫遷移
```bash
# 產生遷移檔案
flask db migrate -m "遷移描述"

# 套用遷移
flask db upgrade

# 查看遷移歷史
flask db history
```

### 除錯工具
```bash
# 執行認證除錯工具
python auth_debug.py

# 執行系統除錯測試
python debug_test.py

# 執行手動功能測試
python manual_functional_test.py
```

### 背景任務 Worker
```bash
# 啟動背景任務 Worker（需先啟動 Redis）
python run_worker.py
```

## 🐳 Docker 部署

### 建立 Docker 映像檔
```bash
docker build -t goat-nutrition-backend .
```

### 使用 Docker Compose
```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs backend
```

## 🔒 安全考量

### 身份驗證
- Flask-Login 會話管理
- 密碼雜湊 (Werkzeug Security)
- CSRF 保護

### 資料驗證
- Pydantic 模型驗證
- SQL 注入防護 (SQLAlchemy ORM)
- 輸入資料清理

### API 安全
- 身份驗證中介軟體
- 錯誤資訊過濾
- 請求速率限制 (建議實施)

## 📝 更新日誌

### v2.1.0 (2025-10-05)
- ✅ 新增 `app/api/traceability.py`，整合產品批次、加工流程與羊隻關聯
- ✅ 擴充 `app/models.py` 與 `schemas.py`，支援公開履歷故事產生
- ✅ 加入 `tests/test_traceability_api.py` 覆蓋批次 CRUD 與公開端權限
- ✅ 公開端 `/api/traceability/public/<批次號>` 進行資料脫敏與安全加固

### v2.0.0 (2025-07-30)
- ✅ 完成 Pydantic V1→V2 遷移
- ✅ 提升測試覆蓋率至 94%
- ✅ 新增 ESG 永續指標支援
- ✅ 優化 AI 代理人回應速度
- ✅ 增強錯誤處理機制

### v1.5.0
- ✅ 整合 Google Gemini AI
- ✅ 實施完整測試套件
- ✅ 新增 Excel 匯入匯出功能
- ✅ 支援 Docker 容器化部署

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](../LICENSE) 檔案

## 📞 技術支援

如有任何技術問題，請透過以下方式聯繫：
- 建立 [GitHub Issue](https://github.com/nj1i6t6/Goat_Nutrition_App_Optimization_Test/issues)
- 發送郵件至專案維護者
