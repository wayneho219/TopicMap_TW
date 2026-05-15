# EventCorr 專案運行狀態檢查 (2026-05-12)

## ✅ 數據管道狀態

### 已完成的步驟
- ✅ **RSS 爬蟲** (`rss_scraper.py`) → `articles.csv`
- ✅ **主題建模 Phase 1** → Topic clustering  
- ✅ **主題建模 Phase 2** → Topic labeling + `output/result_all.csv`
- ✅ **NLP 主題匯入** → SQLite `nlp_topics` & `nlp_topic_stocks` 表

### 數據庫初始化狀態

| 表名 | 行數 | 說明 |
|-----|------|------|
| `tw_stock_list` | 2,314 | 台灣股票清單（來自 tw_stocks.csv） |
| `nlp_topics` | 85 | NLP 主題（25 個 medium + 60 個 fine） |
| `nlp_topic_stocks` | 3,244 | 主題 × 股票關聯 |

## 🚀 运行指南

### 1. 初始化環境
```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 初始化數據庫和導入 NLP 主題
python init_project.py
```

### 2. 啟動後端 API
```bash
cd c:\Users\user\Desktop\EventCorr-main\EventCorr
uvicorn backend.main:app --reload --port 8000
```

**測試端點：**
- `GET /api/market/hot` - 熱門股票排行
- `GET /api/topics?level=medium` - 中級主題列表
- `GET /api/topics/{name}/stocks` - 主題下的股票

### 3. 啟動前端應用
```bash
cd frontend
npm install
npm run dev
```

訪問 `http://localhost:5173` 查看頁面。

---

## 📊 數據流概覽

```
RSS Feeds
   ↓
articles.csv
   ↓
topic_model.py (Phase 1 + Phase 2)
   ↓
output/result_all.csv
   ↓
import_nlp_topics.py
   ↓
tw_stock_list.sqlite3
  ├── nlp_topics (85 topics)
  ├── nlp_topic_stocks (3,244 associations)
  └── tw_stock_list (2,314 stocks)
   ↓
FastAPI Backend
   ↓
React Frontend (localhost:5173)
```

---

## 🔧 可用的初始化腳本

### `init_project.py` - 完整初始化
- 檢查依賴
- 驗證必需的輸入文件
- 嘗試從官方 API 同步股票清單（需要網路連接）
- 嘗試同步股價數據（需要網路連接）
- 導入 NLP 主題
- 驗證數據庫

### `init_stock_list_local.py` - 本地初始化
- 從 `data/tw_stocks.csv` 初始化 `tw_stock_list` 表
- 不需要網路連接
- 用於離線環境

---

## 📋 功能清單

### 後端 API (`backend/main.py`)
- ✅ `/api/market/hot` - 熱門股票（可按成交量、價格、漲幅排序）
- ✅ `/api/market/sectors` - 行業表現
- ✅ `/api/market/sector/{name}/stocks` - 行業內股票詳情
- ✅ `/api/topics` - NLP 主題列表
- ✅ `/api/topics/{name}/children` - 主題層級（medium → fine）
- ✅ `/api/topics/{name}/stocks` - 主題下的股票
- ✅ `/api/stocks/{stock_id}` - 個股詳情
- ✅ `/api/stocks/{stock_id}/intraday` - 盤中行情（即時 Yahoo Finance）
- ✅ `/api/stocks/search` - 股票搜尋

### 前端功能 (`frontend/`)
- ✅ **行情頁面** - 台股/美股/ETF 標籤頁、盤中熱門、熱搜股票
- ✅ **類股分析** - 行業分類 & NLP 主題 toggle
- ✅ **搜尋功能** - 全文搜尋股票代碼/名稱
- ✅ **個股詳情** - 價格圖表、盤中分時線、基本資訊
- ✅ **自選股** - Watchlist 管理

---

## 🐛 已知限制

1. **網路 API 同步** - 股票清單和即時行情需要網路連接
   - 若無網路，使用 `init_stock_list_local.py` 從本地 CSV 初始化
   - 股價數據使用 `tw_stocks.csv` 的快照（2026-04-10）

2. **美股數據** - 目前使用 mock 數據
   - 真實美股數據需要額外配置

3. **地理位置限制** - 某些 API 端點可能受台灣地區限制

---

## 🔄 數據更新流程

### 定期更新股價
```bash
python scripts/tw_stock_quote_sync.py
```

### 更新股票清單（從官方 API）
```bash
python scripts/tw_stock_list_sync.py
```

### 重新訓練 NLP 主題
```bash
# Phase 1: 聚類
python topic_model.py  # 設定 PHASE = "cluster"

# Phase 2: 標籤化
python topic_model.py  # 設定 PHASE = "label"

# 導入到數據庫
python scripts/import_nlp_topics.py
```

---

## 📝 文件結構

```
EventCorr/
├── backend/
│   └── main.py          # FastAPI 應用
├── frontend/
│   ├── src/
│   │   ├── pages/       # React 頁面組件
│   │   ├── hooks/       # 自定義 hooks (API 調用)
│   │   └── components/  # UI 組件
│   └── package.json
├── scripts/
│   ├── tw_stock_list_sync.py     # 同步股票清單
│   ├── tw_stock_quote_sync.py    # 同步股價
│   └── import_nlp_topics.py      # 匯入 NLP 主題
├── data/
│   ├── tw_stock_list.sqlite3    # 主數據庫
│   ├── tw_stocks.csv             # 股票清單快照
│   └── articles.csv              # RSS 爬蟲結果
├── output/
│   ├── result_all.csv            # Phase 2 結果（含主題標籤）
│   ├── tsne_*.html               # t-SNE 視覺化
│   └── tree_*.html               # 層級樹狀圖
├── rss_scraper.py               # RSS 爬蟲
├── topic_model.py               # NLP 主題建模
├── init_project.py              # 完整初始化
└── init_stock_list_local.py     # 本地股票清單初始化
```

---

## ✅ 驗證清單

運行以下命令確保一切正常：

```bash
# 1. 檢查數據庫
python check_db.py

# 2. 測試後端
curl http://localhost:8000/api/topics?level=medium | head -20

# 3. 檢查前端依賴
cd frontend && npm ls --depth=0
```

---

## 🎯 下一步建議

1. **連接真實網路 API**
   - 配置官方 TWSE/TPEx API 授權
   - 每日定時更新股價

2. **優化 NLP 主題**
   - 收集更多新聞文章
   - 微調聚類參數和標籤

3. **添加用户功能**
   - 登入/註冊系統
   - 個人投資組合追蹤
   - 主題訂閱通知

4. **性能優化**
   - 添加數據庫查詢緩存
   - 前端分頁加載
   - 實時行情 WebSocket 連接
