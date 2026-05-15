# DB → Frontend 個股頁串接 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 FastAPI 後端讀取 `tw_stock_list.sqlite3`，讓 `StockDetailPage` 的報價卡顯示真實資料，取代假資料。

**Architecture:** Python FastAPI 提供 `GET /api/stocks/{stock_id}` endpoint；Vite dev server 透過 proxy 轉發前端的 `/api` 請求；React hook `useStock(id)` 封裝 fetch 邏輯，組件只需宣告 hook 使用即可。

**Tech Stack:** Python FastAPI + uvicorn（後端）、React 19 + TypeScript + Vite 8（前端）、SQLite（資料庫）、pytest + httpx（後端測試）

---

## 檔案清單

| 動作 | 路徑 | 說明 |
|---|---|---|
| 新增 | `backend/main.py` | FastAPI app，含 `/api/stocks/{stock_id}` endpoint |
| 新增 | `tests/test_backend.py` | 後端 API 單元測試 |
| 新增 | `frontend/src/hooks/useStock.ts` | React hook，封裝 fetch 與 loading/error 狀態 |
| 修改 | `frontend/src/pages/StockDetailPage.tsx` | 改用 `useStock` hook，移除 `mockStockDetail` 引用 |
| 修改 | `frontend/vite.config.ts` | 加入 `/api` proxy 到 `http://localhost:8000` |

---

## Task 1: 安裝後端依賴

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 安裝 fastapi 與 uvicorn**

```bash
pip install "fastapi==0.115.12" "uvicorn[standard]==0.34.3" "httpx==0.28.1"
```

Expected output: `Successfully installed fastapi-... uvicorn-... httpx-...`

- [ ] **Step 2: 寫入 requirements.txt**

在 `requirements.txt` 末尾加入三行：

```
fastapi==0.115.12
uvicorn[standard]==0.34.3
httpx==0.28.1
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add fastapi uvicorn httpx dependencies"
```

---

## Task 2: 建立 FastAPI 後端（TDD）

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_backend.py`

- [ ] **Step 1: 建立 backend 目錄與空的 main.py**

```bash
mkdir -p backend
touch backend/__init__.py backend/main.py
```

- [ ] **Step 2: 先寫失敗測試**

建立 `tests/test_backend.py`，內容如下：

```python
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app

client = TestClient(app)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

def test_get_stock_known():
    """2330 台積電應存在於 DB，回傳 200 並含必要欄位"""
    resp = client.get('/api/stocks/2330')
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == '2330'
    assert isinstance(data['price'], float)
    assert isinstance(data['change'], float)
    assert isinstance(data['changePercent'], float)
    assert isinstance(data['volume'], int)
    assert data['name'] != ''
    assert isinstance(data['tags'], list)
    assert len(data['tags']) >= 1

def test_get_stock_not_found():
    """不存在的股票代號應回傳 404"""
    resp = client.get('/api/stocks/9999')
    assert resp.status_code == 404

def test_get_stock_twse_tags():
    """TWSE 上市股票 tags 應含「上市」"""
    resp = client.get('/api/stocks/2330')
    assert resp.status_code == 200
    assert '上市' in resp.json()['tags']

def test_get_stock_tpex_tags():
    """上櫃股票 tags 應含「上櫃」（用已知上櫃代號 6547）"""
    resp = client.get('/api/stocks/6547')
    if resp.status_code == 200:
        assert '上櫃' in resp.json()['tags']
    # 若 DB 沒有此代號則跳過（不強制）
```

- [ ] **Step 3: 執行測試確認失敗**

```bash
pytest tests/test_backend.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`（因為 `backend/main.py` 是空的）

- [ ] **Step 4: 實作 `backend/main.py`**

```python
import sqlite3
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

MARKET_LABEL = {
    'TWSE_LISTED': '上市',
    'TPEX_OTC': '上櫃',
    'TPEX_EMERGING': '興櫃',
}

def _tags(market: str) -> list[str]:
    label = MARKET_LABEL.get(market, market)
    if market == 'TWSE_LISTED':
        return [label, '可現沖']
    return [label]

def _parse_float(val) -> float:
    """'+0.30' or '-1.20' or 1.5 → float"""
    if val is None:
        return 0.0
    return float(str(val).replace('+', '').replace('%', ''))

@app.get('/api/stocks/{stock_id}')
def get_stock(stock_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            'SELECT * FROM tw_stock_list WHERE stock_code = ?', (stock_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail='Stock not found')

    return {
        'id': row['stock_code'],
        'name': row['stock_name'],
        'price': float(row['close_price']) if row['close_price'] is not None else 0.0,
        'change': _parse_float(row['change_val']),
        'changePercent': _parse_float(row['change_pct']),
        'volume': int(row['volume']) if row['volume'] is not None else 0,
        'market': row['market'],
        'industry': row['industry_name'],
        'tags': _tags(row['market']),
        'status': '已收盤',
        'high': None,
        'low': None,
        'prevClose': None,
        'open': None,
    }
```

- [ ] **Step 5: 執行測試確認通過**

```bash
pytest tests/test_backend.py -v
```

Expected:
```
tests/test_backend.py::test_get_stock_known PASSED
tests/test_backend.py::test_get_stock_not_found PASSED
tests/test_backend.py::test_get_stock_twse_tags PASSED
tests/test_backend.py::test_get_stock_tpex_tags PASSED
```

- [ ] **Step 6: Commit**

```bash
git add backend/__init__.py backend/main.py tests/test_backend.py
git commit -m "feat(backend): add GET /api/stocks/{stock_id} endpoint"
```

---

## Task 3: 建立 `useStock` hook

**Files:**
- Create: `frontend/src/hooks/useStock.ts`

- [ ] **Step 1: 建立 hooks 目錄與 useStock.ts**

```bash
mkdir -p frontend/src/hooks
```

建立 `frontend/src/hooks/useStock.ts`：

```typescript
import { useState, useEffect } from 'react'

export interface StockDetail {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  market: string
  industry: string
  tags: string[]
  status: string
  high: number | null
  low: number | null
  prevClose: number | null
  open: number | null
}

interface UseStockResult {
  stock: StockDetail | null
  loading: boolean
  error: string | null
}

export function useStock(id: string | undefined): UseStockResult {
  const [stock, setStock] = useState<StockDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setError('無效的股票代號')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    fetch(`/api/stocks/${id}`)
      .then((res) => {
        if (res.status === 404) throw new Error('找不到股票')
        if (!res.ok) throw new Error('伺服器錯誤')
        return res.json()
      })
      .then((data: StockDetail) => {
        setStock(data)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }, [id])

  return { stock, loading, error }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useStock.ts
git commit -m "feat(frontend): add useStock hook"
```

---

## Task 4: 修改 StockDetailPage.tsx

**Files:**
- Modify: `frontend/src/pages/StockDetailPage.tsx`

- [ ] **Step 1: 更新 import，加入 useStock**

在 `StockDetailPage.tsx` 頂端，找到這行：

```typescript
import { mockStockDetail, mockChartData } from '../data/mock'
```

替換為：

```typescript
import { mockChartData } from '../data/mock'
import { useStock } from '../hooks/useStock'
```

- [ ] **Step 2: 在 StockDetailPage 函式內加入 hook，加入 loading/error 畫面**

找到：

```typescript
export function StockDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [chartTab, setChartTab] = useState(0)
  const [timeTab, setTimeTab] = useState(0)
  const [brokerTopTab, setBrokerTopTab] = useState(0)
  const stock = mockStockDetail
```

替換為：

```typescript
export function StockDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [chartTab, setChartTab] = useState(0)
  const [timeTab, setTimeTab] = useState(0)
  const [brokerTopTab, setBrokerTopTab] = useState(0)
  const { stock, loading, error } = useStock(id)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#111111]">
        <div className="w-8 h-8 rounded-full border-2 border-[#2dba6a] border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !stock) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#111111] gap-3">
        <span className="text-[#888] text-sm">{error ?? '找不到股票'}</span>
        <button onClick={() => navigate(-1)} className="text-[#2dba6a] text-sm">返回</button>
      </div>
    )
  }
```

- [ ] **Step 3: 修正 null 欄位的顯示**

找到價格資訊格的 grid 區塊（最高/最低/昨收/開盤）：

```typescript
          <div className="grid grid-cols-2 gap-y-1.5 text-sm">
            <div className="flex gap-2">
              <span className="text-[#888]">最高</span>
              <span className="text-[#e84040] font-medium">{stock.high.toFixed(2)}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">昨收</span>
              <span className="text-white font-medium">{stock.prevClose.toFixed(2)}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">最低</span>
              <span className="text-[#e84040] font-medium">{stock.low.toFixed(2)}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">開盤</span>
              <span className="text-[#e84040] font-medium">{stock.open.toFixed(2)}</span>
            </div>
          </div>
```

替換為：

```typescript
          <div className="grid grid-cols-2 gap-y-1.5 text-sm">
            <div className="flex gap-2">
              <span className="text-[#888]">最高</span>
              <span className="text-[#e84040] font-medium">{stock.high != null ? stock.high.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">昨收</span>
              <span className="text-white font-medium">{stock.prevClose != null ? stock.prevClose.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">最低</span>
              <span className="text-[#e84040] font-medium">{stock.low != null ? stock.low.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">開盤</span>
              <span className="text-[#e84040] font-medium">{stock.open != null ? stock.open.toFixed(2) : '—'}</span>
            </div>
          </div>
```

- [ ] **Step 4: 確認 KLineTab 呼叫傳入 prevClose 的地方**

找到：

```typescript
        {chartTab === 0 && <KLineTab timeTab={timeTab} setTimeTab={setTimeTab} prevClose={stock.prevClose} />}
```

替換為：

```typescript
        {chartTab === 0 && <KLineTab timeTab={timeTab} setTimeTab={setTimeTab} prevClose={stock.prevClose ?? stock.price} />}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/StockDetailPage.tsx
git commit -m "feat(frontend): wire StockDetailPage to useStock hook"
```

---

## Task 5: 加入 Vite proxy

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: 修改 vite.config.ts**

找到：

```typescript
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

替換為：

```typescript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/vite.config.ts
git commit -m "feat(frontend): add vite proxy for /api"
```

---

## Task 6: 整合測試（手動 smoke test）

- [ ] **Step 1: 啟動後端**

```bash
uvicorn backend.main:app --reload --port 8000
```

確認輸出含：`Application startup complete.`

- [ ] **Step 2: 在另一個 terminal 啟動前端**

```bash
cd frontend && npm run dev
```

確認輸出含：`Local: http://localhost:5173`

- [ ] **Step 3: 瀏覽器測試**

開啟 `http://localhost:5173/stock/2330`，確認：
- 標題列顯示 `(2330) 台積電`（非假資料的 `0050 元大台灣50`）
- 報價顯示真實收盤價
- 最高/最低/昨收/開盤欄位顯示 `—`（null fallback）
- 走勢圖正常顯示（mock data）
- 無 console error

開啟 `http://localhost:5173/stock/9999`，確認：
- 顯示「找不到股票」提示與返回按鈕

- [ ] **Step 4: Commit（若無需修正則跳過）**

若 smoke test 發現問題，修正後：

```bash
git add -p
git commit -m "fix(frontend): <描述問題>"
```
