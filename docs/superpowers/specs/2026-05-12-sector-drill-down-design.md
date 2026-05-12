# Spec: 類股 Accordion 鑽取層級設計

**日期：** 2026-05-12
**功能範圍：** 行情 → 類股 tab 的「類股」view 改為兩層 accordion，並整合 tpex_industry_chain 與 NLP 主題補充

---

## 背景與目標

現行「類股」tab 的類股 view 為一層平面列表（`tw_stock_list.industry_name`），點擊直接進入個股列表。使用者希望類股可以像「主題」tab 一樣支援層級鑽取：先看大類，再展開看細分主題，最後進個股列表。

目標：
- 第一層：`tpex_industry_chain.major_industry`（固定大類，如數位科技、綠色能源）
- 第二層：`tpex_industry_chain.chain_topic`（概念股鏈）+ LLM 篩選後的 NLP fine 主題（即時補充）
- 第三層：個股列表（reuse 現有頁面）

---

## 整體架構

```
tpex_industry_chain DB              tw_stock_list DB           nlp_topics DB
  major_industry                      price / volume             nlp_topics (fine)
  chain_topic          ──────────→    即時行情計算         ←──  nlp_topic_stocks
  stock_code
                                                          ↑
                                                   LLM 分類腳本
                                              (is_industry + major_industry 映射)
                                                          ↓
                                               nlp_topic_industry_map（新表）
```

---

## §1 DB Schema

在 `tw_stock_list.sqlite3` 新增一張分類結果表：

```sql
CREATE TABLE nlp_topic_industry_map (
    topic_id           INTEGER PRIMARY KEY REFERENCES nlp_topics(id),
    is_industry        INTEGER NOT NULL DEFAULT 0,   -- 1=產業相關, 0=雜訊
    major_industry     TEXT,                          -- NULL 表示非產業主題
    classified_at      TEXT NOT NULL
);
```

- `topic_id` 對應 `nlp_topics.id`（fine level），一對一
- `major_industry` 值域鎖定為 `tpex_industry_chain.major_industry` 現有清單
- 重跑分類使用 `INSERT OR REPLACE`

---

## §2 LLM 分類腳本

**檔案：** `scripts/classify_nlp_topics.py`

**流程：**
1. 讀取所有 `nlp_topics WHERE level='fine'` 且尚未分類（`LEFT JOIN nlp_topic_industry_map` 過濾）
2. 讀取 `tpex_industry_chain` 的 `major_industry` 清單作為固定選項
3. 呼叫 Claude API，prompt 結構：

```
以下是 NLP 聚類出的股市主題名稱："{topic_name}"

請判斷：
1. 是否為產業/行業主題（非閒聊、情緒、政治類）？
2. 若是，最接近以下哪個大類（只能選一個，或回 null）：
   {major_industry_list}

請用 JSON 回覆：{"is_industry": true/false, "major_industry": "xxx" or null}
```

4. 結果寫入 `nlp_topic_industry_map`
5. 使用 prompt caching 減少 token 消耗（major_industry 清單放 cached block）
6. 使用模型：`claude-haiku-4-5-20251001`（分類任務不需要強模型，降低成本）

**執行方式：**
```bash
python scripts/classify_nlp_topics.py
```

支援增量執行（只處理未分類的主題）。

---

## §3 後端 API

舊有 `/api/market/sectors`、`/api/market/sector/{name}/stocks`、`/api/market/chain/{name}/stocks` 保持不動。

### `GET /api/market/industries?sort=change&order=desc`

Query params（選填）：`sort=change|volume`，`order=asc|desc`，預設 `sort=change&order=desc`。

回傳 major_industry 列表，附帶聚合行情：

```json
[
  {
    "name": "數位科技",
    "topicCount": 7,
    "advance": 12,
    "decline": 8,
    "changePercent": 1.23
  }
]
```

**計算邏輯：**
- 從 `tpex_industry_chain` 取 major_industry 底下所有 stock_code
- JOIN `tw_stock_list` 取即時 change_pct
- 計算 avg changePercent、advance/decline 數量
- topicCount = chain_topic 數量 + is_industry=1 的 NLP 主題數量

### `GET /api/market/industry/{name}/topics`

回傳該 major_industry 底下所有子主題：

```json
[
  { "name": "人工智慧", "source": "tpex",  "changePercent": 2.1,  "stockCount": 15 },
  { "name": "雲端運算", "source": "tpex",  "changePercent": -0.5, "stockCount": 9  },
  { "name": "AI伺服器散熱", "source": "nlp", "changePercent": 3.2, "stockCount": 7  }
]
```

- `source: "tpex"` → chain_topic，stock_code 來自 `tpex_industry_chain`
- `source: "nlp"` → NLP fine 主題，stock 來自 `nlp_topic_stocks`，需 `is_industry=1` 且 `major_industry=name`
- `changePercent` 皆從 `tw_stock_list` 即時計算
- 依 `changePercent` 絕對值降序排列

---

## §4 前端 UI

### Hook

```typescript
// useIndustries()：呼叫 /api/market/industries
// useIndustryTopics(name)：展開時才呼叫 /api/market/industry/{name}/topics
```

### 組件結構

```
SectorTab（修改）
├── 移除原有的 useSectors() 呼叫與排序 UI（改用新 accordion 取代）
├── useIndustries()
├── IndustryCard（新組件，仿 MediumCard）
│   ├── accordion header：major_industry 名稱 + changePercent + 漲跌數量
│   ├── useIndustryTopics()（只在展開時呼叫）
│   └── TopicRow（新組件，仿 FineRow）
│       ├── tpex 主題：無 badge
│       └── NLP 主題：加 `✦` 小 badge 區分
```

### UI 行為

```
┌─────────────────────────────────────┐
│ 數位科技              +1.23%  ›     │  ← 點擊展開/收起
│ ████████░░░░ 7個主題  漲12 跌8      │
└─────────────────────────────────────┘
  ├ 人工智慧          +2.1%  15支
  ├ 雲端運算          -0.5%   9支
  └ AI伺服器散熱 ✦    +3.2%   7支    ← NLP 補充，badge 標記
```

- 一次只展開一個 major_industry（同現有主題 tab）
- 預設依 `changePercent` 絕對值降序排列

### 導航

| 點擊目標 | 導航 |
|---|---|
| `source: "tpex"` 子主題 | `/sector/chain/:name` → SectorDetailPage（chain 模式，已有） |
| `source: "nlp"` 子主題 | `/topic/fine/:name` → TopicDetailPage（已有） |

---

## §5 不變動的部分

- `TopicTab`（主題 tab）完全不動
- `SectorDetailPage` 邏輯不動
- `TopicDetailPage` 不動
- `/api/market/sectors` 等舊 API 不動
- `tw_stock_list.industry_name` 現有平面 sector 邏輯不動（兩套並存，類股 view 改用新 API）

---

## 實作順序建議

1. DB migration：建立 `nlp_topic_industry_map` 表
2. LLM 分類腳本：`scripts/classify_nlp_topics.py`
3. 後端 API：`/api/market/industries` 和 `/api/market/industry/{name}/topics`
4. 前端 hook：`useIndustries`、`useIndustryTopics`
5. 前端 UI：`IndustryCard`、`TopicRow`、修改 `SectorTab`
