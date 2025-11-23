# 《領頭羊博士》前端風格指南 · Aurora Biophilic 2.0

> 依據《領頭羊博士》前端體驗優化與視覺升級 · 終極藍圖 2.0 (整合版) 制訂。

## 視覺語彙

- **核心風格**：極光仿生科技（Aurora Biophilic Tech）融合玻璃擬態（Glassmorphism）。
- **色彩系統**：於 `src/styles/tokens/aurora-theme.css` 定義的 CSS Design Tokens，提供光源漸層、霧面玻璃背景、系統提示色與互動陰影。
- **字體與排版**：預設字體為 `Noto Sans TC` / `Inter`，搭配 `--aurora-transition-base` 控制動態節奏。透過 `data-font-scale` 屬性配合 `settings` store 調整字級。
- **暗色模式**：`data-theme="dark"` 採用深海紫藍色背景與高反差文字，與淺色模式共享 Accent 色彩。

## 全域樣式

- `src/assets/styles/main.css` 為全域樣式入口，會引入 Aurora Token，提供背景漸層、Glass Surface helper (`.aurora-glass-surface`) 與 Element Plus 調整。
- 請避免在個別元件覆寫 Token，可透過自訂 CSS 變數或 `:root[data-theme]` 擴充。

## 元件抽象層

### BaseAuroraCard
- 路徑：`src/components/common/BaseAuroraCard.vue`
- 功能：提供 Aurora 玻璃卡片容器，支援 `title`、`subtitle`、`icon`、`actions` slot。
- 用法：所有資訊卡與統計卡請優先使用該容器以保持陰影、圓角與 hover 動效一致。

### AsyncChartWrapper
- 路徑：`src/components/common/AsyncChartWrapper.vue`
- 功能：結合 `IntersectionObserver` 與 `defineAsyncComponent`，在圖表即將進入 viewport 時才載入真正的圖表元件，並提供骨架屏與錯誤提示。
- API：
  - `loader`：回傳 Promise 的函式，用於動態載入圖表 renderer。
  - `componentProps`：轉交給實際圖表 renderer 的屬性。
  - `delay`、`timeout`、`errorTitle`、`errorSubtitle`：客製化異步行為與錯誤訊息。

### useLazyCharts
- 路徑：`src/composables/useLazyCharts.js`
- 功能：封裝 ECharts 的懶載入、IntersectionObserver 與資源回收。
- 回傳：`ensureChart`、`dispose`、`refresh`、`loading` 等狀態，可在 renderer 內部呼叫以確保僅在需要時初始化 ECharts。

### VirtualizedLogTable
- 路徑：`src/components/tables/VirtualizedLogTable.vue`
- 功能：整合 Element Plus `el-table-v2` 虛擬滾動與增量載入，以 `useActivityLogStore` 管理 Pinia 狀態，支援 `loadMoreOffset`、自訂欄位與快取降級顯示。

## 狀態管理

- `src/stores/theme.js`：負責深/淺色與 Aurora 動效開關，狀態透過 `useTheme` composable 提供給任何元件。
- `src/stores/activityLog.js`：活動日誌的虛擬滾動資料來源，對後端 `/api/activity/logs` 介面做容錯，初期會提供 fallback sample 資料避免畫面空白。
- `src/composables/useTheme.js`：提供 `toggleColorScheme`、`toggleMotion`、`auroraAccentClass` 等方法與派生狀態，並同步 `<meta name="theme-color">`。

## 佈局整合

- `AppLayout.vue` 使用 Aurora 導覽列與漸層背景，右上角新增主題/動效控制按鈕。
- 主內容區域 `main-content` 採用動態漸層背景與更寬鬆的 padding，確保 Glass 卡片的陰影與光暈不被裁切。

## 實作準則

1. **圖表**：在 Analytics 等頁面使用 `AsyncChartWrapper` + renderer（位於 `analytics/renderers/`）結合 `useLazyCharts`。請避免在頁面層直接初始化 ECharts。
2. **資料密集視圖**：優先使用 `VirtualizedLogTable` 或 `el-table-v2`，並確保滾動事件觸發 Pinia store 的 `fetchNextPage` 以配合藍圖的 Infinite Scroll 要求。
3. **動效與效能**：尊重 `data-aurora-motion` 設定；新增動畫前，應檢查 `useTheme().motionEnabled` 或 CSS 變數是否允許。
4. **色彩**：使用 Token (`--aurora-*`) 而非硬編碼，並確保暗色模式對比度合格。
5. **文件同步**：新增元件後請更新本指南，保持藍圖與實作一致。

## 後續建議

- 建立 Storybook 或 VitePress 元件範例頁，對 `BaseAuroraCard`、`AsyncChartWrapper`、`VirtualizedLogTable` 等核心元件提供可視化說明。
- 與後端協調 `/api/activity/logs` 規格，替換暫時的 fallback 資料，並在 `docs/glossary.md` 補充「Aurora 動效」、「活動日誌」等詞彙。
