---
type: source
title: SA.md — AI 投資決策室願景文件
tags: [pipeline, taiwan-stock, concept-stock, supply-chain, sentiment]
raw: SA.md
ingested: 2026-05-05
authors: [wayneho219]
---

# SA.md — AI 投資決策室願景文件

## 核心主張

系統以**「零預算、高自動化、重文本」**為架構原則，整合：
- 結構化量化財務數據（行情、財報）
- 非結構化市場輿情文本（PTT 討論）

目標產出：台股「概念股標籤」+ 「資金流向」的自動萃取。

## 兩個模組

### 1. 資料萃取模組
- PTT Stock 看板爬蟲（目前實作：`rss_scraper.py`）
- 對每支股票以股票代號搜尋，取前 N 篇，支援斷點續跑

### 2. 階層分群模組
- `topic_model.py` 執行 NLP 主題分群
- 依 `tw_stocks.csv` 產業分類作為第一層（固定）
- NLP 自動分群作為第二層（medium）、第三層（fine）

## 最終願景

```
NLP 主題標籤（result_all.csv）
        ×
每日行情/成交量（tw_stock_list.sqlite3）
        ↓
資金熱門的供應鏈 / 概念股排行
```

## 與現況的落差

此願景尚未實現——合併 NLP 標籤與行情資料的層並不存在。詳見 [[pipeline-current-state]]。
