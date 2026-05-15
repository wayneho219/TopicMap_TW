# TopicMap TW — 台股主題地圖

以 AI 驅動的台股新聞事件分析管線，將 PTT Stock 看板文章與個股行情串接，透過 NLP 主題建模識別概念股群組與供應鏈主題，並以行動風格前端 App 呈現。

---

## 專案架構

```
PTT Stock 看板
      ↓
pipeline/rss_scraper.py（文章抓取 + STOPWORDS 噪音過濾）
      ↓
articles.csv（~48萬篇文章）
      ↓
pipeline/topic_model.py Phase 1：BGE embedding → UMAP → Ward 分群
      ↓
data/labels/label_template.json（人工/LLM 命名）
      ↓
pipeline/topic_model.py Phase 2：標籤套用 + yfinance 股價抓取
      ↓
output/result_all.csv（含 close_price / volume / invested_amount）
      ↓
scripts/import_nlp_topics.py（冪等 CSV → SQLite）
      ↓
data/tw_stock_list.sqlite3
  ├── tw_stock_list（即時行情）
  ├── nlp_topics（25 中層 + 60 細層主題）
  └── nlp_topic_stocks（主題 × 個股關聯）
      ↓
backend/（FastAPI，Router / Service / Repository 三層架構）
      ↓
frontend（React + TypeScript + Vite + Tailwind）
```

---

## 技術棧

| 層次 | 工具 |
|------|------|
| 文章爬取 | `feedparser`、PTT Web API |
| Embedding | BGE-large-zh-v1.5（1024d）via `sentence-transformers` |
| 降維 | UMAP（15d）→ T-SNE（2d） |
| 分群 | Ward 階層分群（`scipy`） |
| 股價抓取 | `yfinance`（`.TW` ticker，近 2 年） |
| 資料庫 | SQLite（`tw_stock_list.sqlite3`） |
| 後端 | FastAPI + Pydantic v2，Router / Service / Repository 三層 OOP |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 路由 | `react-router-dom` |

---

## 安裝

```bash
# Python 依賴
pip install -r requirements.txt

# topic_model.py 額外依賴
pip install feedparser sentence-transformers umap-learn scikit-learn jieba yfinance

# 前端依賴
cd frontend && npm install
```

---

## 執行 Pipeline

### Step 1：文章爬取

```bash
python pipeline/rss_scraper.py
```

輸出：`articles.csv`（欄位：`stock_id`, `ArticleTitle`, `Tags`, `ArticleText`, `ArticleCreateTime`）

### Step 2a：主題建模 Phase 1（分群）

```bash
# 設定 PHASE = "cluster"（pipeline/topic_model.py 頂部）
python pipeline/topic_model.py
# 輸出：data/labels/label_input.txt、data/labels/label_template.json
```

### Step 2b：命名後執行 Phase 2（標籤 + 股價）

```bash
# 填寫 data/labels/topic_labels.json 後，設定 PHASE = "label"
python pipeline/topic_model.py
# 輸出：output/result_all.csv（含 invested_amount）
#       output/invested_amount_medium.csv / fine.csv
#       output/tsne_*.html、output/tree_*.html 等視覺化
```

### Step 3：匯入 SQLite

```bash
python scripts/import_nlp_topics.py
# 建立/更新 nlp_topics（85筆）與 nlp_topic_stocks
```

---

## 啟動服務

**後端**（port 8000）：

```bash
uvicorn backend.main:app --reload --port 8000
```

**前端**（port 5173）：

```bash
cd frontend && npm run dev
```

開啟 `http://localhost:5173`

---

## 前端功能

| 頁面 | 說明 |
|------|------|
| 行情（MarketPage） | 台股 / 美股 / ETF 熱門排行；類股 Tab 含「類股 / 主題」切換 |
| 類股（SectorTab）| 各產業漲跌幅 + 成交量排行，可下鑽個股 |
| 主題（TopicTab）| NLP 分群的 25 個中層主題 accordion，投入金額視覺化；展開可見 60 個細層主題 |
| 主題詳情（TopicDetailPage） | 主題下的個股列表，支援漲跌幅 / 成交量 / 討論熱度排序 |
| 自選（WatchlistPage） | 個人追蹤清單 |
| 股票詳情（StockDetailPage） | 個股行情 + 歷史走勢 |

---

## 後端 API

| 端點 | 說明 |
|------|------|
| `GET /api/market/hot` | 熱門股票排行（可篩選市場、類型、排序） |
| `GET /api/market/search_hot` | 搜尋框熱門推薦 |
| `GET /api/market/recurring/tw` | 定期定額熱門 ETF |
| `GET /api/market/sectors` | 類股漲跌幅排行 |
| `GET /api/market/sector/{name}/stocks` | 類股下個股列表 |
| `GET /api/market/chain/{name}/stocks` | 供應鏈主題下個股 |
| `GET /api/market/industries` | 產業統計（含 NLP / 供應鏈主題數） |
| `GET /api/market/industry/{name}/stocks` | 產業下個股列表 |
| `GET /api/market/industry/{name}/topics` | 產業相關主題（tpex + nlp） |
| `GET /api/stocks/prices` | 批次查詢個股報價 |
| `GET /api/stocks/search` | 股票搜尋 |
| `GET /api/stocks/{id}` | 個股詳情 |
| `GET /api/stocks/{id}/topics` | 個股所屬 NLP 主題 |
| `GET /api/stocks/{id}/intraday` | 個股當日分時資料 |
| `GET /api/topics` | NLP 主題列表（`?level=medium\|fine`，依投入金額排序） |
| `GET /api/topics/{name}/children` | 中層主題的細層子項 |
| `GET /api/topics/{name}/stocks` | 主題下個股（支援排序） |

---

## 測試

```bash
python -m pytest tests/ -v
```

---

## 目錄結構

```
TopicMap_TW/
├── pipeline/
│   ├── rss_scraper.py          # 文章爬取
│   ├── topic_model.py          # NLP 主題建模
│   └── dashboard.py            # 資料儀表板
├── scripts/
│   ├── import_nlp_topics.py    # CSV → SQLite 匯入
│   ├── tw_stock_quote_sync.py  # 行情同步
│   └── tpex_industry_chain_scraper.py  # 供應鏈資料爬取
├── backend/
│   ├── main.py                 # FastAPI app（精簡，只做組裝）
│   ├── database.py             # DB 連線 context manager
│   ├── schemas.py              # Pydantic response models
│   ├── repositories/           # DB 查詢層
│   ├── services/               # 業務邏輯層
│   └── routers/                # API 路由層
├── frontend/                   # React + TypeScript 前端
├── data/
│   ├── tw_stock_list.sqlite3   # 主資料庫
│   └── labels/                 # 主題標籤（label_template.json 等）
├── wiki/                       # LLM 知識庫
└── tests/                      # 測試
```
