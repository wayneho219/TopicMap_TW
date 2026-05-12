---
type: source
title: 管線現況分析（2026-05-05）
tags: [pipeline, open-question]
raw: null
ingested: 2026-05-05
authors: [wayneho219]
---

# 管線現況分析（2026-05-05）

## 已完成的部分

### 資料收集
- `articles.csv`：~48 萬行 PTT 文章（`stock_id`, `ArticleTitle`, `ArticleText`, `ArticleCreateTime`）
- `result_all.csv`：12,194 筆，含 25 個中層主題 + 60 個細層主題
- `data/tw_stock_list.sqlite3`：2,314 支股票，含 `close_price`、`change_pct`、`volume`、`quote_date`
- `data/tpex_industry_chain.sqlite3`：6,909 筆 TPEX 產業鏈對應資料

### 分群結果
目前已有一版完整的主題標籤（見 [[topic-labels-v1]]）。60 個細層主題涵蓋：概念股討論、月營收公告、財報揭露、版規管理、技術操作等類別。

## 三大斷層

| 斷層 | 說明 |
|------|------|
| **腳本名稱誤導** | `rss_scraper.py` 實際是 PTT 爬蟲，CLAUDE.md 寫的是 RSS |
| **手動兩段式管線** | `topic_model.py` 靠頂部 `PHASE` 變數切換，需手動改程式碼才能重跑 |
| **資料孤島** | `scripts/` 產出的行情/產業鏈資料完全未接進主管線 |

## 最優先待辦

1. 把 `result_all.csv` 與 `tw_stock_list.sqlite3` 做 JOIN，輸出含漲跌幅的結果
2. `topic_model.py` 改 CLI 參數（`--phase cluster/label`），移除手動改碼的步驟
3. Phase 1→2 的人工命名可用 Claude API 自動化

## 相關概念頁
- [[eventcorr-pipeline]] — 整體架構圖
- [[topic-labels-v1]] — 目前標籤版本
