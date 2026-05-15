# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TopicMap TW** is an AI-driven data pipeline for Taiwan stock market analysis. It correlates news events with individual stock performance by:
1. Scraping RSS financial news feeds and tagging articles to matching stocks
2. Running hierarchical topic modeling (NLP clustering) on article text to identify concept stock groups and supply chain themes

There is a secondary pipeline described in [docs/SA.md](docs/SA.md) — an "AI Investment Decision Room" focused on dynamic stock labeling and sentiment analysis for Taiwan stocks (台股).

## Setup

### Python Dependencies

Install core dependencies:
```bash
pip install -r requirements.txt
```

Additional packages required by `pipeline/topic_model.py`:
```bash
pip install feedparser sentence-transformers umap-learn scikit-learn jieba yfinance
```

### Frontend Dependencies

```bash
cd frontend && npm install
```

### Database

`data/tw_stock_list.sqlite3` is the primary database. It contains:
- `tw_stock_list` — real-time market data
- `nlp_topics` — 25 medium-level + 60 fine-level topics
- `nlp_topic_stocks` — topic × stock associations

## Running the Pipeline

The complete data pipeline flows: RSS → articles.csv → topic modeling → labels → SQLite → API → frontend.

### Step 1: RSS Scraping (`pipeline/rss_scraper.py`)

```bash
python pipeline/rss_scraper.py
```

Outputs `articles.csv` with columns: `stock_id`, `ArticleTitle`, `Tags`, `ArticleText`, `ArticleCreateTime`.

Core function: `fetch_and_process_rss(rss_urls, stock_dict)` — takes RSS URL list and stock-to-keyword mapping. Built-in sample feeds are available for testing.

To load the full market stock list from CSV per [scripts/transform.py](scripts/transform.py):
```bash
python scripts/transform.py
```

### Step 2: Topic Modeling (`pipeline/topic_model.py`)

Controlled by `PHASE` variable at the top of the file.

**Phase 1 — Cluster:**
```bash
# Set PHASE = "cluster" at top of pipeline/topic_model.py, then:
python pipeline/topic_model.py
# Outputs: data/labels/label_input.txt (for human/LLM labeling), data/labels/label_template.json
```

**Phase 2 — Label & Stock Price:**
```bash
# 1. Fill in data/labels/label_template.json, save as data/labels/topic_labels.json
# 2. Set PHASE = "label" at top of pipeline/topic_model.py, then:
python pipeline/topic_model.py
# Outputs: output/result_all.csv (with invested_amount), output/tsne_*.html, output/tree_*.html, etc.
```

**Input:** `articles.csv` with columns `ArticleText`, `ArticleCreateTime`, `StockId`.

**Caching:** Embeddings cached to `cache/_embeddings.npy`. Delete to force re-embedding.

### Step 3: Import to SQLite (`scripts/import_nlp_topics.py`)

```bash
python scripts/import_nlp_topics.py
```

Imports Phase 2 outputs into `tw_stock_list.sqlite3` (idempotent). Creates/updates `nlp_topics` (85 topics) and `nlp_topic_stocks` tables.

### Dashboard (`pipeline/dashboard.py`)

```bash
python pipeline/dashboard.py
```

## Architecture

### Data Flow

```
RSS Feeds → pipeline/rss_scraper.py → articles.csv
                                            ↓
                          pipeline/topic_model.py (Phase 1: cluster)
                                            ↓
                          data/labels/label_input.txt / data/labels/label_template.json
                                            ↓
                          [Human/LLM labels → data/labels/topic_labels.json]
                                            ↓
                          pipeline/topic_model.py (Phase 2: label)
                                            ↓
                    output/result_all.csv + output/*.html visualizations
```

### Topic Modeling Pipeline (pipeline/topic_model.py)

1. **Embedding** — BGE-large-zh-v1.5 (1024d) via `sentence-transformers`
2. **Dim reduction** — UMAP (15d) → T-SNE (2d for visualization)
3. **Clustering** — Ward hierarchical clustering on UMAP embeddings
4. **Multi-level cutting** — Three granularity levels: coarse / medium / fine
5. **Auto-detection** — Calinski-Harabasz score selects optimal cluster counts (when `AUTO_LEVELS=True`)
6. **Keyword extraction** — TF-IDF + jieba tokenization per cluster
7. **Visualization** — Interactive HTML: scatter plots, icicle/treemap/sunburst hierarchy charts, dendrogram

## Running the Application

### Backend (FastAPI)

```bash
uvicorn backend.main:app --reload --port 8000
```

Key endpoints:
- `GET /api/market/hot` — hot stock rankings
- `GET /api/market/sectors` — sector performance
- `GET /api/stocks/{id}` — individual stock details
- `GET /api/topics?level=medium|fine` — NLP topics (sorted by invested amount)
- `GET /api/topics/{name}/stocks` — stocks in a topic

### Frontend (React + Vite)

```bash
cd frontend && npm run dev
```

Opens at `http://localhost:5173`. Built with React 18, TypeScript, Vite, Tailwind CSS, and react-router-dom.

Pages:
- **Market** — hot stocks; sector/topic tabs
- **Sector** — industry performance + stock drilldown
- **Topic** — 25 medium-level topics with accordion; expandable to 60 fine-level topics
- **Topic Detail** — stocks in a topic; sortable by return/volume/discussion
- **Stock Detail** — individual stock with historical price chart
- **Watchlist** — personal tracking list

## Testing

```bash
python -m pytest tests/ -v
```

Test files cover backend APIs, NLP topic classification, database imports, and dashboard functionality.

## LLM Wiki

Project maintains a knowledge base at `wiki/`:
- Read `wiki/SCHEMA.md` before browsing
- Use `wiki/index.md` to find pages
- Log changes in `wiki/log.md`

## Generated / Temporary Files (not committed)

- `cache/_embeddings.npy` — cached sentence embeddings
- `cache/_checkpoint.parquet` — DataFrame with Phase 2 cluster assignments
- `cache/_cluster_{level}.npy` — cluster arrays (coarse/medium/fine)
- `cache/_linkage.npy` — Ward linkage matrix for dendrogram
- `output/` — Phase 2 visualizations (HTML) and results (CSV)
