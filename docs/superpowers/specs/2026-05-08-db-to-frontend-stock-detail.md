# Design: DB → Frontend 串接（個股頁優先）

**Date:** 2026-05-08
**Scope:** StockDetailPage 報價卡串接真實資料；圖表保留 mock

---

## 目標

建立 FastAPI 後端，讀取 `data/tw_stock_list.sqlite3`，提供 REST API 給 React 前端的 `StockDetailPage` 使用，取代目前的假資料。

---

## 後端（`backend/main.py`）

### Endpoint

```
GET /api/stocks/{stock_id}
```

**Response schema：**
```json
{
  "id": "2330",
  "name": "台積電",
  "price": 1025.0,
  "change": 25.0,
  "changePercent": 2.5,
  "volume": 198700,
  "market": "上市",
  "industry": "半導體業",
  "tags": ["上市", "可現沖"],
  "status": "已收盤",
  "high": null,
  "low": null,
  "prevClose": null,
  "open": null
}
```

**欄位來源對照（`tw_stock_list` 資料表）：**

| Response 欄位 | DB 欄位 | 備註 |
|---|---|---|
| id | stock_code | |
| name | stock_name | |
| price | close_price | |
| change | change_val | |
| changePercent | change_pct | |
| volume | volume | |
| market | market | |
| industry | industry_name | |
| tags | market | `上市` → `["上市","可現沖"]`；`上櫃` → `["上櫃"]` |
| status | — | 固定回傳 `"已收盤"` |
| high/low/prevClose/open | — | 固定回傳 `null` |

**找不到時：** 回傳 HTTP 404

### CORS
開放 `http://localhost:5173`（Vite dev server）

### 啟動方式
```bash
cd backend
uvicorn main:app --reload --port 8000
```

---

## 前端

### 新增：`frontend/src/hooks/useStock.ts`

封裝 fetch 邏輯，對外暴露：
```ts
{ stock: StockDetail | null, loading: boolean, error: string | null }
```

- `StockDetail` interface 對應 API response schema
- `high / low / prevClose / open` 型別為 `number | null`，前端顯示時 fallback 為 `"—"`

### 修改：`frontend/src/pages/StockDetailPage.tsx`

- 移除 `mockStockDetail` 的引用
- 改用 `useStock(id)` hook
- loading 狀態：顯示灰色 skeleton placeholder
- error / 404：顯示「找不到股票」文字提示
- 圖表（`mockChartData`）不動

### 修改：`frontend/vite.config.ts`

加入 proxy 設定：
```ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

---

## 不在此 scope 內

- 分時走勢圖串接真實資料
- 券商分點資料（`BrokerTab`）
- 其他頁面（MarketPage、WatchlistPage 等）
- 使用者認證
- 部署
