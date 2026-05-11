---
type: source
title: NLP 主題分類整合實作（2026-05-11）
tags: [pipeline, nlp, topic-modeling, taiwan-stock]
created: 2026-05-11
updated: 2026-05-11
authors: [wayne-dev, claude-subagents]
raw: docs/superpowers/plans/2026-05-09-nlp-topic-integration.md
ingested: 2026-05-11
---

# NLP 主題分類整合實作（2026-05-11）

## 摘要

本次實作將 `daniel-dev` 分支的 NLP 主題分類資料（`invested_amount`）完整串接至前端展示。覆蓋 12 個 task，涉及資料管線、SQLite、後端 API、前端 UI 四層。

## 各層變更

### 1. 資料管線層

**`rss_scraper.py`**
- 新增 `STOPWORDS` 常數（法人買賣超、月營收公告、財報公告、公告垃圾、注意股、股票抽籤 6 類）
- 在文章加入 `batch` 前過濾含停用詞的標題，減少噪音進入 pipeline

**`topic_model.py` Phase 2**
- 新增 `import yfinance as yf`
- Phase 2 label 步驟完成後，針對每個 `stock_id` 抓取近 2 年股價（`.TW` ticker）
- 為每篇文章匹配最近交易日收盤價，計算 `invested_amount = close_price × volume`
- `result_all.csv` 新增 3 欄：`close_price`、`volume`、`invested_amount`
- 新增 `output/invested_amount_medium.csv`、`output/invested_amount_fine.csv` 統計 CSV

### 2. 資料庫層

**`scripts/import_nlp_topics.py`**（新增，冪等）
- 讀取 `output/result_all.csv`，寫入 `data/tw_stock_list.sqlite3` 的兩張新表
- `nlp_topics`：主題維度表（medium + fine 兩層），含 `total_invested`、`article_count`、`stock_count`
- `nlp_topic_stocks`：主題 × 股票關聯表，含 `total_invested`、`article_count`
- 冪等設計：每次執行先 `DROP TABLE IF EXISTS`，重建後重新填入
- 真實 DB 匯入結果：25 個 medium 主題、60 個 fine 主題

**測試**：`tests/test_import_nlp_topics.py`（6 個測試，全數通過）

### 3. 後端 API 層

**`backend/main.py`** 新增 3 個端點：

| 端點 | 說明 |
|------|------|
| `GET /api/topics?level=medium\|fine` | 依 `total_invested` DESC 排序回傳主題列表；`level` 無效回 400 |
| `GET /api/topics/{name}/children` | 回傳指定 medium 主題的 fine 子主題；找不到回 404 |
| `GET /api/topics/{name}/stocks?level=&sort=heat\|change\|volume&order=asc\|desc` | 回傳主題下個股，支援三種排序；找不到回 404 |

回應格式：camelCase（`totalInvested`、`articleCount`、`stockCount` 等）。

**測試**：`tests/test_topics_api.py`（7 個測試，全數通過）

### 4. 前端層

| 檔案 | 類型 | 說明 |
|------|------|------|
| `frontend/src/hooks/useTopics.ts` | 新增 | `useTopics`、`useTopicChildren`、`useTopicStocks` 三個 hook |
| `frontend/src/components/TopicTab.tsx` | 新增 | medium 主題 accordion，展開顯示 fine 子主題，進度條視覺化投入金額 |
| `frontend/src/pages/MarketPage.tsx` | 修改 | SectorTab 加入「類股 / 主題」toggle，切換後渲染 `<TopicTab />` |
| `frontend/src/pages/TopicDetailPage.tsx` | 新增 | 主題個股列表頁，支援漲跌幅 / 成交量 / 討論熱度三種排序 |
| `frontend/src/App.tsx` | 修改 | 新增 `/topic/:level/:name` 路由，`hideBottomNav` 加入 `/topic/` 條件 |

## DB 結構（新增）

```sql
nlp_topics (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  level TEXT CHECK(level IN ('medium','fine')),
  parent_id INTEGER REFERENCES nlp_topics(id),
  total_invested REAL,
  article_count INTEGER,
  stock_count INTEGER
)

nlp_topic_stocks (
  topic_id INTEGER REFERENCES nlp_topics(id) ON DELETE CASCADE,
  stock_code TEXT NOT NULL,
  article_count INTEGER,
  total_invested REAL,
  PRIMARY KEY (topic_id, stock_code)
)
```

## 測試摘要

- 全體後端測試：**29/29 通過**
- TypeScript 型別：無錯誤（`npx tsc --noEmit`）
- Frontend build 阻擋錯誤：已修正（`import type` for `Topic`、`TopicSortKey`）

## 已知限制

- `yfinance` 抓取速度較慢（逐股 API，無批次），適合離線 batch 運行，不適合即時
- `nlp_topics` 若 DB 尚未執行 import，後端 API 回傳 sqlite OperationalError（可考慮加 try/except）
- `STOPWORDS` 過濾目前只比對標題（`art["title"]`），尚未過濾內文

## 關聯頁面

- [[eventcorr-pipeline]] — 管線架構（本次大幅擴充）
- [[topic-labels-v1]] — 已整合至 DB 的主題標籤資料
- [[nlp-topic-api]] — 新後端 API 說明
