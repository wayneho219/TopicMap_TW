# Wiki 操作日誌

操作的時序記錄（僅附加）。每筆以 `## [YYYY-MM-DD] <op> | <描述>` 開頭，可用 `grep "^## \[" log.md | tail -N` 解析。

操作類型：
- `ingest` — 來源已處理並入 wiki。
- `query` — 已針對 wiki 回答問題（通常僅在結果歸檔為 synthesis 時記錄）。
- `lint` — 已執行健康檢查。
- `schema` — 已修改 schema。
- `shard` — 索引已拆分。

---

## [2026-05-05] schema | 初始化 EventCorr wiki 結構
## [2026-05-05] ingest | SA.md → sources/sa-vision.md（願景文件摘要）
## [2026-05-05] ingest | 管線現況分析 → sources/pipeline-current-state.md（三大斷層 + 資料盤點）
## [2026-05-05] ingest | topic_labels.json → entities/topic-labels-v1.md（60 細層 / 25 中層主題）
## [2026-05-05] ingest | 架構分析 → concepts/eventcorr-pipeline.md（資料流 + 技術棧）
## [2026-05-05] ingest | 雜訊過濾分析 → sources/noise-filter-analysis.md（filter.py 322 篇，誤分類發現）
## [2026-05-06] ingest | dashboard.py 設計完成 → docs/superpowers/specs/2026-05-06-dashboard-design.md
## [2026-05-11] ingest | NLP 主題整合實作 → sources/nlp-topic-integration-impl-2026-05-11.md（yfinance + DB import + API + 前端，29 測試通過）
## [2026-05-11] update | concepts/eventcorr-pipeline.md — 資料流更新至含 nlp_topics DB + 前端
## [2026-05-11] update | entities/topic-labels-v1.md — 加入 DB 整合狀態與 invested_amount 說明
## [2026-05-11] ingest | concepts/nlp-topic-api.md 新增（端點規格 + 前端架構）
