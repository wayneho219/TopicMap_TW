# 📈 AI 投資決策室：台股動態標籤與情緒分析系統 (Data Pipeline)

## 📝 專案概述 (Project Overview)
本專案旨在為「AI 多智能體投資決策室」建立底層的自動化資料管線 (Data Pipeline)。系統以 **「零預算、高自動化、重文本」** 為核心架構原則，整合結構化的量化財務數據與非結構化的市場輿情文本，自動萃取出台股「概念股標籤」與「資金流向」，可以根據 topic_model 細分出概念股或產業鏈，再結合交易量與漲跌幅，觀察資金熱門的供應鏈或概念股。

本專案分為資料萃取模組與階層分群模組。

---

## ✅ 已實現成果（截至 2026-05-11）

### 資料管線

| 模組 | 狀態 | 說明 |
|------|------|------|
| PTT 文章爬取（`rss_scraper.py`） | ✅ 完成 | 含 STOPWORDS 雜訊過濾（法人買賣超、財報公告等 6 類） |
| NLP 主題建模（`topic_model.py`） | ✅ 完成 | BGE-large-zh-v1.5 → UMAP → Ward 分群，Phase 1/2 雙階段 |
| yfinance 股價整合 | ✅ 完成 | Phase 2 自動抓取每篇文章對應日期的收盤價與成交量 |
| invested_amount 指標 | ✅ 完成 | `close_price × volume`，作為「話題資金熱度」代理指標 |
| SQLite 匯入（`import_nlp_topics.py`） | ✅ 完成 | 冪等設計；建立 `nlp_topics`（85筆）、`nlp_topic_stocks` 兩表 |

### 主題建模成果

- **25 個中層主題**：含電子科技、航運、生技、傳產、財務公告等大類
- **60 個細層主題**：含 AI液冷記憶體、台積電供應鏈、低軌衛星等概念股群組
- **資金熱度排行**：每個主題計算 `total_invested`（億元），可直接排序呈現

### 後端 API（FastAPI）

| 端點 | 功能 |
|------|------|
| `/api/topics?level=medium\|fine` | 依投入金額排序的主題列表 |
| `/api/topics/{name}/children` | 中層主題展開細層 |
| `/api/topics/{name}/stocks` | 主題下個股，支援漲跌幅 / 成交量 / 討論熱度排序 |

### 前端 App（React + TypeScript）

- **行情首頁**：台股 / 美股 / ETF 熱門排行
- **類股 Tab**：類股漲跌幅 / 成交量排行（支援下鑽）
- **主題 Tab（NLP 成果）**：25 個中層主題 accordion，展開細層子主題，以投入金額進度條視覺化
- **主題詳情頁**：個股列表，三種排序方式切換
- **個股詳情頁**：行情走勢 + 基本資料

---

## 🗺️ 系統架構圖

```
PTT Stock 看板文章（~48萬筆）
          ↓
  rss_scraper.py（爬取 + 過濾）
          ↓
     articles.csv
          ↓
 topic_model.py（NLP 管線）
  ├─ Phase 1: 分群（BGE + UMAP + Ward）
  └─ Phase 2: 命名 + 股價（yfinance）
          ↓
 result_all.csv（含 invested_amount）
          ↓
 import_nlp_topics.py → SQLite
          ↓
   FastAPI 後端（/api/topics）
          ↓
   React 前端（TopicTab + TopicDetailPage）
```

---

## 🔭 後續方向

- 情緒分析層：對概念股討論文章進行正負面評分
- 即時化：將 PTT 爬取改為定時排程，行情與主題每日更新
- 供應鏈整合：將 `tpex_industry_chain.sqlite3` 接入 API，補充產業鏈維度
- AI 決策室：多智能體框架，結合主題熱度 + 情緒 + 籌碼給出投資建議




