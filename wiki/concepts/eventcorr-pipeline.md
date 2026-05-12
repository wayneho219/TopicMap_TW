---
type: concept
title: EventCorr 管線架構
tags: [pipeline, nlp, taiwan-stock]
created: 2026-05-05
updated: 2026-05-11
sources: [sa-vision, pipeline-current-state, nlp-topic-integration-impl-2026-05-11]
---

# EventCorr 管線架構

## 資料流

```
PTT Stock 看板
      ↓
rss_scraper.py（實為 PTT 爬蟲）
  └─ STOPWORDS 過濾標題噪音（2026-05-11 新增）
      ↓
articles.csv（~48萬行）
      ↓
topic_model.py ── Phase 1: cluster
      ↓
label_input.txt + label_template.json
      ↓
[人工 / LLM 命名] → topic_labels.json
      ↓
topic_model.py ── Phase 2: label
  └─ yfinance 股價抓取（2026-05-11 新增）
  └─ 新增 close_price / volume / invested_amount 欄位
      ↓
result_all.csv（含 invested_amount）+ HTML 視覺化
  + invested_amount_medium.csv / invested_amount_fine.csv
      ↓
scripts/import_nlp_topics.py（2026-05-11 新增，冪等）
      ↓
tw_stock_list.sqlite3（新增 nlp_topics + nlp_topic_stocks 表）
      ↓
backend/main.py（/api/topics 端點群）
      ↓
前端 TopicTab accordion + TopicDetailPage
```

## 現有接入的資料

```
scripts/tw_stock_quote_sync.py → tw_stock_list.sqlite3（行情）✓
scripts/import_nlp_topics.py → tw_stock_list.sqlite3（NLP 主題）✓（2026-05-11）
scripts/tpex_industry_chain_scraper.py → tpex_industry_chain.sqlite3（產業鏈）待接
```

## topic_model.py 技術棧

| 步驟 | 工具 | 說明 |
|------|------|------|
| 文字清理 | jieba + regex | 去 URL、去非中英數符號 |
| Embedding | BGE-large-zh-v1.5（1024d） | `sentence-transformers` |
| 降維 | UMAP（15d）→ T-SNE（2d） | 分群用 UMAP，視覺化用 T-SNE |
| 分群 | Ward 階層分群 | `scipy.cluster.hierarchy` |
| 關鍵詞 | TF-IDF + jieba | 每群取 top-15 中文詞 |
| 視覺化 | Plotly | Sunburst / Treemap / Icicle / Dendrogram |

## 快取機制

| 檔案 | 內容 | 何時失效 |
|------|------|---------|
| `_embeddings.npy` | BGE embedding 結果 | 手動刪除可強制重算 |
| `_checkpoint.parquet` | Phase 1 結果，供 Phase 2 讀取 | 每次 Phase 1 重跑後更新 |
| `_cluster_*.npy` | 各層分群 label array | 同上 |
| `_linkage.npy` | Ward linkage matrix | 同上 |

## 已知問題

- `PHASE` 變數寫死在程式頂部，需手動改碼才能切換階段
- Phase 1→2 命名步驟是唯一的人工瓶頸
- `yfinance` 逐股抓取，速度慢，不適合即時；適合離線 batch
- `nlp_topics` 若 DB 尚未 import，後端 API 會拋 `sqlite3.OperationalError`（尚未加 try/except 保護）
- `STOPWORDS` 目前只過濾標題，未過濾內文

## 關聯頁面

- [[nlp-topic-api]] — 新後端 API + 前端整合詳情
- [[topic-labels-v1]] — 已匯入 DB 的主題標籤
