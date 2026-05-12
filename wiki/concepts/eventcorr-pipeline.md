---
type: concept
title: EventCorr 管線架構
tags: [pipeline, nlp, taiwan-stock]
created: 2026-05-05
updated: 2026-05-05
sources: [sa-vision, pipeline-current-state]
---

# EventCorr 管線架構

## 資料流

```
PTT Stock 看板
      ↓
rss_scraper.py（實為 PTT 爬蟲）
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
      ↓
result_all.csv + HTML 視覺化
```

## 現有但未接入的資料

```
scripts/tw_stock_quote_sync.py → tw_stock_list.sqlite3（行情）
scripts/tpex_industry_chain_scraper.py → tpex_industry_chain.sqlite3（產業鏈）
```

這兩條支線**尚未與主管線合併**，是實現 [[sa-vision]] 的關鍵缺口。

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
