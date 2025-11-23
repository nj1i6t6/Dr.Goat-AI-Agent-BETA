# Terminology Glossary

| English Term | zh-TW Term | Notes |
|--------------|-----------|-------|
| Sheep | 羊隻 | Core animal entity managed across modules. |
| Flock | 羊群 | Grouping used in dashboards and reports. |
| Batch | 批次 | Production batch for traceability workflows. |
| Traceability | 產銷履歷 | Public-facing supply-chain storytelling. |
| Verifiable Ledger | 可驗證賬本 | Append-only hash chain stored in `verifiable_log`. |
| Data Fingerprint | 數據指紋 | Modal showing hash/metadata for traceability steps. |
| ESG | 永續 / ESG 指標 | Environmental, social, and governance metrics. |
| Sensor Reading | 感測數據 | IoT ingestion payload stored per device. |
| IoT Device | IoT 裝置 | Managed hardware endpoint for telemetry. |
| Automation Rule | 自動化規則 | Maps sensor triggers to actuator commands. |
| Background Task | 背景任務 | Redis-backed job executed by `run_worker.py`. |
| Dashboard Cache | 儀表板快取 | Redis layer for cached analytics widgets. |
| API Key | API 金鑰 | Must be hashed server-side; shown once to users. |
| Growth Prediction | 生長預測 | ML-powered forecast served via `/api/prediction`. |
| Daily Tip | 每日提示 | Gemini-generated guidance for caretakers. |
| Intake Form | 匯入表單 | Excel-powered batch data ingestion forms. |
| Pinia Store | Pinia Store 狀態 | Vue global state container. |
| Element Plus | Element Plus 元件庫 | Frontend UI component library. |
| Worker Queue | 佇列 | Redis queue feeding the worker process. |
| Alembic Migration | 資料庫遷移 | Schema migration script under `backend/migrations/`. |
| Coverage Report | 覆蓋率報告 | Stored under `docs/backend/coverage/` and `docs/frontend/coverage/`. |
| Cost Entry | 成本紀錄 | Ledger row stored via `CostEntry` model/API. |
| Revenue Entry | 收益紀錄 | Ledger row stored via `RevenueEntry` model/API. |
| Cohort Analysis | 分群分析 | `/api/bi/cohort-analysis` 聚合結果。 |
| Cost-Benefit Dashboard | 成本效益分析 | `/api/bi/cost-benefit` 匯總結果與 KPI。 |
| Nutrition & ESG Guidance | 營養與ESG建議 | Navigation label for the consultation workflow that collects sheep context and returns AI recommendations. |
| Dr.Goat Q&A | 羊博士問答 | Chat assistant surface branded for conversational Q&A and multimodal uploads. |
| Sheep Management | 羊群管理 | Navigation label for the flock overview, CRUD flows, and consultation shortcuts. |
| Data Analytics Center | 數據分析中心 | Vue view that consolidates KPIs, cohort charts, finance entries, and AI-generated reports. |

Maintain this glossary whenever terminology changes in the English SoT or zh-TW documentation.
