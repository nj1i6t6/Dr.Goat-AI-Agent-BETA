docker run -p 80:80 goat-nutrition-frontend
docker-compose up -d frontend
describe('FieldHelper', () => {
describe('Auth Store', () => {
describe('API Client', () => {
# 領頭羊博士 - 前端指南

> Vue 3 SPA，搭配 Pinia、Vue Router、Element Plus 與 Chart.js/ECharts，提供 AI 諮詢、羊隻管理、儀表板與預測體驗。

## 1. 快速概覽

- **框架**：Vue 3.x + Composition API，建構工具為 Vite 7。
- **狀態**：Pinia stores（auth、sheep、dashboard、chat、consultation、settings、traceability）。
- **圖表**：Chart.js + vue-chartjs、ECharts 5。
- **測試**：Vitest + @vue/test-utils + happy-dom。
- **部署**：多階段 Dockerfile，Nginx 服務 SPA 與 API 代理。

最新實測（2025-10-05）
- 測試：`npm run test -- --run`、`npx vitest run traceability`。
- 覆蓋率：`npm run test:coverage -- --run`（Statements 約 82%，HTML 報告：`../../docs/frontend/coverage/index.html`）。

## 2. 目錄速覽

```
frontend/
├── src/
│   ├── api/            # Axios client + 模組化端點
│   ├── components/     # 共用元件（含 FieldHelper、Sheep*）
│   ├── router/         # 路由守衛、懶載入
│   ├── stores/         # Pinia (auth/sheep/chat/traceability/...)
│   ├── utils/          # errorHandler、formatters 等
│   └── views/          # Dashboard、Chat、DataManagement...
├── public/             # favicon、靜態資產
├── docs/               # （本檔）
├── vite.config.js      # HMR + `/api` 代理 → `http://127.0.0.1:5001`
├── vitest.config.*.js  # 多種測試配置
├── Dockerfile          # 多階段建構 + Nginx
└── nginx.conf          # SPA 回退、壓縮、快取、代理
```

Pinia stores 皆以 `defineStore` 建立，並利用 `localStorage` 與後端 Cookie Session 維持登入狀態；路由守衛會偵測 `meta.requiresAuth`。

## 3. 關鍵模組

- **`src/api/index.js`**：集中設定 Axios（`withCredentials: true`、401 自動登出）。
- **`src/views/*`**：頁面層組件，以懶載入降低初始 bundle。
- **`src/components/sheep/`**：羊隻 CRUD 流程（表格、篩選、分頁 tabs）。
- **`src/views/PredictionView.vue`**：ECharts 視覺化與 AI 說明。
- **`src/views/ChatView.vue`**：支援文字/圖片上傳，使用 Markdown-It 呈現。
- **`src/views/DataManagementView.vue`**：整合 Excel 上傳、進度條、錯誤彙整。
- **`src/views/TraceabilityManagementView.vue`**：產品批次與加工流程管理，支援羊隻貢獻設定與公開連結複製。
- **`src/views/TraceabilityPublicView.vue`**：面向消費者的公開履歷頁，以時間軸呈現加工流程。
- **`src/stores/chat.js`**：管理 Gemini 會話、歷史與載入狀態。
- **`src/stores/traceability.js`**：集中管理批次、步驟、羊隻關聯與公開資料同步。

## 4. 建置與開發

### 本機開發（PowerShell）
```
cd frontend
npm install
npm run dev
# 預設 http://localhost:5173，透過 Vite 代理轉送 /api -> http://127.0.0.1:5001
```

### 生產建置
```
npm run build
npm run preview  # 驗證 dist 內容
```

### Docker 多階段
- `FROM node:20-alpine` → `npm ci` + `npm run build`
- `FROM nginx:alpine`  → 複製 `dist/` 與 `nginx.conf`
- 暴露 80/4173；`nginx.conf` 支援 gzip、SPA fallback、`/api` proxy。

## 5. 測試與覆蓋率

```
npm run test              # 標準 Vitest（happy-dom）
npm run test:coverage     # 產生 V8 coverage + HTML
npx vitest run traceability  # 無監聽模式執行產銷履歷 store 測試
npm run test:ui           # 啟動 Vitest UI（選配）
npm run test:isolated     # 迴避循環依賴的個別配置
```

- 覆蓋率結果會同步輸出到 `coverage/` 與 `../../docs/frontend/coverage/`。
- 測試夾具 `src/test/setup-unified.js` 負責註冊全域 mock、Element Plus 組件設定。
- API 測試仰賴 `msw`/mock server？（目前主要以 axios mock 與 happy-dom 模擬）。

## 6. 常見操作

- **調整 API 位置**：設定 `VITE_API_BASE_URL`（在 `env` 或 Docker `proxy_pass`）。
- **登入狀態自動還原**：`useAuthStore` 會在 `beforeEach` 透過 localStorage 重新 hydrate。
- **開發模式下引用真實後端**：確保後端啟動於 5001，或調整 `vite.config.js` 代理。
- **CI 建置建議**：`npm ci` → `npm run build` → `npm run test:coverage`，可在 `dist/` 與 `docs/frontend/coverage/` 保存成果。

## 7. 故障排除

| 狀況 | 排查提示 |
|------|-----------|
| 首頁白屏 | 檢查 `npm run dev` 日誌、瀏覽器 Console，確認 `router` 懶載入與 Element Plus 匯入無錯。 |
| 登入跳回登入頁 | 後端未設定 CORS 或 Cookie，或 `X-Requested-With` 被移除。確認代理與後端 `SESSION_COOKIE_SAMESITE='None'`。 |
| API `401` 立即登出 | 這是預期行為：Axios interceptor 會調用 `authStore.logout()`。請確認憑證或放寬 mock。 |
| 圖表顯示空白 | 確認後端 `/api/prediction/...` 回傳資料格式；ECharts 需要 `markRaw` 包裝以避免 Proxy。 |

## 8. 更新日誌與引用

- 最新文件：2025-09-25。
- 覆蓋率報告：`../../docs/frontend/coverage/index.html`。
- 參考文件：`../../docs/README.md`、`../../docs/Development.md`。
- 授權：MIT（見專案根目錄 `LICENSE`）。

---

調整頁面或 store 後，請同步更新對應測試並重新產出覆蓋率，再將報告置於 `docs/frontend/coverage/` 供檢視。
