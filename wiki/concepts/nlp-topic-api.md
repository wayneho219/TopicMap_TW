---
type: concept
title: NLP 主題 API 與前端整合
tags: [pipeline, nlp, topic-modeling, taiwan-stock]
created: 2026-05-11
updated: 2026-05-11
sources: [nlp-topic-integration-impl-2026-05-11]
---

# NLP 主題 API 與前端整合

本頁說明 2026-05-11 新增的 NLP 主題後端端點及前端 UI 架構。

## 後端 API 端點

所有端點讀取 `tw_stock_list.sqlite3` 的 `nlp_topics` / `nlp_topic_stocks` 兩張表。

### `GET /api/topics?level=medium|fine`

回傳指定層級的所有主題，依 `total_invested` DESC 排序。
- `level` 非 `medium` 或 `fine` 時回傳 **400**。

```json
[
  {
    "id": 1,
    "name": "AI半導體",
    "level": "medium",
    "parentId": null,
    "totalInvested": 854467864250.49,
    "articleCount": 187,
    "stockCount": 25
  }
]
```

### `GET /api/topics/{name}/children`

回傳指定 medium 主題的 fine 子主題列表（依 `total_invested` DESC）。
- 找不到對應的 medium 主題時回傳 **404**。

### `GET /api/topics/{name}/stocks?level=medium|fine&sort=heat|change|volume&order=asc|desc`

回傳主題下的個股清單（JOIN `tw_stock_list`，只含有收盤價的股票）。
- `sort` 預設 `heat`（按文章數）；`change` 按漲跌幅；`volume` 按成交量。
- 找不到主題回 **404**；`level` 無效回 **400**。

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

## 前端架構

```
MarketPage（行情 → 類股 tab）
  └─ SectorTab
       ├─ [類股] toggle → 原有類股排行
       └─ [主題] toggle → <TopicTab />
                              ├─ MediumCard（accordion，可展開）
                              │    └─ FineRow（細層主題，點擊進 TopicDetailPage）
                              └─ MediumCard 右箭頭 → TopicDetailPage（medium）

TopicDetailPage（/topic/:level/:name）
  └─ useTopicStocks()
       ├─ 排序：漲跌幅 / 成交量 / 討論熱度（含升降冪）
       └─ 個股列表 → 點擊進 StockDetailPage
```

## React Hooks

| Hook | 回傳 | 說明 |
|------|------|------|
| `useTopics(level)` | `Topic[]` | 對應 `GET /api/topics` |
| `useTopicChildren(name)` | `Topic[]` | 對應 `GET /api/topics/{name}/children` |
| `useTopicStocks(name, level, sort, order)` | `{ stocks, loading }` | 對應 `GET /api/topics/{name}/stocks` |

三個 hook 均有 `.catch()` fallback，API 失敗時回傳空陣列。

## 視覺設計要點

- 主題卡片以**水平進度條**視覺化 `totalInvested`，最高主題佔滿寬度
- 投入金額格式化：≥ 1 億顯示「N 億」，≥ 1 萬顯示「N 萬」
- 顏色系統沿用全站：漲 `#e84040`、跌 `#2dba6a`、強調 `#3a7bd5`

## 關聯頁面

- [[eventcorr-pipeline]] — 整體管線架構，含 DB import 步驟
- [[topic-labels-v1]] — 已匯入的主題標籤詳情
