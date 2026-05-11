# NLP 主題分類整合設計

**日期：** 2026-05-09  
**分支來源：** 合併 `daniel-dev` 的 NLP pipeline 輸出 → 存入 DB → 顯示於前端

---

## 背景

`daniel-dev` 分支在 `topic_model.py` 的 PHASE="label" 階段新增了：
- yfinance 抓取各股票歷史股價和成交量
- 計算每篇文章的「投入金額」= 收盤價 × 成交量
- 輸出 `result_all.csv`（stock_id / label_medium / label_fine / invested_amount 等）
- 輸出 `invested_amount_medium.csv` / `invested_amount_fine.csv`（各主題總投入金額）

目標：將此分類資料存入現有 SQLite，並在前端 MarketPage 的「類股」tab 中以 accordion 形式展示 NLP 主題。

---

## 資料規模

| 項目 | 數量 |
|------|------|
| result_all.csv 筆數 | 2,166 筆 |
| 涉及股票數 | 828 支 |
| medium 主題數 | 25 個 |
| fine 主題數 | 60 個 |

---

## DB Schema

**位置：** `data/tw_stock_list.sqlite3`（方案 A，與現有股票資料同一 DB）

```sql
CREATE TABLE nlp_topics (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    level          TEXT    NOT NULL CHECK(level IN ('medium', 'fine')),
    parent_id      INTEGER REFERENCES nlp_topics(id),  -- fine 指向 medium；medium 為 NULL
    total_invested REAL    NOT NULL DEFAULT 0,
    article_count  INTEGER NOT NULL DEFAULT 0,
    stock_count    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_nlp_topics_level  ON nlp_topics(level);
CREATE INDEX idx_nlp_topics_parent ON nlp_topics(parent_id);

CREATE TABLE nlp_topic_stocks (
    topic_id       INTEGER NOT NULL REFERENCES nlp_topics(id) ON DELETE CASCADE,
    stock_code     TEXT    NOT NULL,
    article_count  INTEGER NOT NULL DEFAULT 0,
    total_invested REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (topic_id, stock_code)
);

CREATE INDEX idx_nlp_topic_stocks_code ON nlp_topic_stocks(stock_code);
```

**hierarchy：**
- `nlp_topics` level='medium' → `parent_id = NULL`
- `nlp_topics` level='fine' → `parent_id` 指向對應 medium row 的 id
- fine 與 medium 的對應關係由 `result_all.csv` 的 `label_medium` / `label_fine` 欄位推導

---

## 資料匯入腳本

**位置：** `scripts/import_nlp_topics.py`

**邏輯：**
1. 讀取 `output/result_all.csv`（需已存在，由 topic_model.py Phase 2 產出；daniel-dev 原放根目錄，已對齊至 output/）
2. DROP + CREATE `nlp_topics` / `nlp_topic_stocks`（冪等，可重複執行）
3. 建立 medium 主題列表，計算 total_invested / article_count / stock_count
4. 建立 fine 主題列表，設定 parent_id 指向對應 medium
5. 建立 nlp_topic_stocks（topic_id × stock_code，匯總 article_count / total_invested）
6. 連接 `data/tw_stock_list.sqlite3` 寫入

**執行方式：**
```bash
python scripts/import_nlp_topics.py
```

---

## 後端 API（`backend/main.py` 新增）

### `GET /api/topics`

| 參數 | 型別 | 預設 | 說明 |
|------|------|------|------|
| level | string | medium | 'medium' 或 'fine' |

回傳：主題列表，按 `total_invested DESC`

```json
[
  {
    "name": "AI半導體",
    "level": "medium",
    "totalInvested": 854467864250.49,
    "articleCount": 187,
    "stockCount": 25
  }
]
```

### `GET /api/topics/{name}/children`

回傳：指定 medium 主題下的所有 fine 子主題（同上結構），按 `total_invested DESC`

### `GET /api/topics/{name}/stocks`

| 參數 | 型別 | 預設 | 說明 |
|------|------|------|------|
| level | string | medium | 查哪一層的主題 |
| sort | string | heat | 'change' / 'volume' / 'heat' |
| order | string | desc | 'asc' / 'desc' |

回傳：該主題內的股票列表，JOIN `tw_stock_list` 取現價

```json
[
  {
    "id": "2330",
    "name": "台積電",
    "price": 1000.0,
    "change": 35.0,
    "changePercent": 3.5,
    "volume": 42000000,
    "articleCount": 42,
    "topicInvested": 461413362216.5
  }
]
```

**排序邏輯：**
- `change`：按 `change_pct` 排序（來自 tw_stock_list）
- `volume`：按 `volume` 排序（來自 tw_stock_list）
- `heat`：按 `nlp_topic_stocks.article_count` 排序

---

## 前端設計

### MarketPage — SectorTab 改造

在 `SectorTab` 頂部加入 toggle：

```
[ 類  股 ]  [● 主  題 ]
```

- 預設顯示類股（維持現有行為）
- 切換主題時，顯示 `TopicTab` component

### TopicTab — 主題列表（accordion）

```
 AI半導體           8,544億
 ████████░░░░░░░░    100%
 25支 · 187篇                       ▶（展開）
   ├─ 台積電股      4,614億
   │   ████████░░    54%
   │   12支 · 42篇                  →（進個股頁）
   └─ 消費電子      3,446億
       ██████░░░░    40%
       8支 · 35篇                   →（進個股頁）
 短線博弈           5,505億         ▶
 ...
```

**互動規則：**
- 點 medium 主題 card → 展開/收合 fine 子主題列表（accordion，單展一個）
- 點 fine 子主題 → 導航至 `TopicDetailPage`
- 點 medium 主題名稱右側的「→」符號 → 直接進入 medium 主題的個股列表

### TopicDetailPage（新頁面）

路由：`/topic/:level/:name`

```
← AI半導體（主題）

[ 漲跌幅 ▼ ]  [ 成交量 ]  [ 討論熱度 ]

  1  台積電    1000  +3.50%
     投入金額 4,614億 · 討論 42 篇
  ────────────────────────────────
  2  聯發科     820  +2.10%
     投入金額  892億 · 討論 18 篇
  ...
```

---

## 合併 daniel-dev 的其他改動

### topic_model.py
- 新增 yfinance 股價抓取段落（Phase 2 label 後執行）
- 新增 invested_amount 欄位計算
- 輸出 `result_all.csv` / `invested_amount_*.csv` / `topics_*.csv`
- 注意：輸出路徑對齊到 `output/` 目錄（daniel-dev 放在根目錄，需修正）

### rss_scraper.py
- 新增 `STOPWORDS` 清單（法人買賣超、月營收、財報公告、注意股、股票抽籤等垃圾訊號）

---

## 不在本次範圍

- 美股主題（無資料來源）
- 主題標籤的自動更新排程（需 NLP pipeline 重跑）
- 主題搜尋功能

---

## 完成標準

1. `scripts/import_nlp_topics.py` 執行後，DB 中可查到 25 個 medium + 60 個 fine 主題
2. `GET /api/topics` 回傳正確主題列表
3. MarketPage 類股 tab 可切換到主題 accordion
4. 點 fine 主題 → TopicDetailPage 顯示正確個股列表（含現價）
5. 排序切換（漲跌幅 / 成交量 / 討論熱度）正常運作
