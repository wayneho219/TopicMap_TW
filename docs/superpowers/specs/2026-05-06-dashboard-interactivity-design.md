# Dashboard 互動化設計文件

**日期：** 2026-05-06
**專案：** EventCorr 概念股監控儀表板
**範圍：** 將靜態 HTML 改寫為 Dash 應用，首先實作跨圖表聯動（Feature A）

---

## 背景與目標

現有 `dashboard.py` 輸出一份靜態 HTML，內含三個獨立的 Plotly 圖表（熱度排行、散點圖、個股表格）。使用者的核心需求是：

1. 了解目前哪個產業主題討論最熱
2. 找出因應熱度有轉型跡象的個股

靜態圖表無法回答「這個主題下有哪些個股、它們的漲跌如何」這種需要聯動的問題。

---

## 技術選型

**Dash（Plotly）**

- 與現有 Plotly 圖表原生整合，`go.Figure` 直接沿用
- 可完整控制 CSS 外觀，維持國泰品牌主題
- Callback 機制天然支援跨元件聯動
- 啟動指令：`python dashboard.py`，預設開在 `http://localhost:8050`

---

## 視覺主題規格

| 項目 | 值 |
|---|---|
| 背景色 | `#FAFBFA`（頁面）/ `#FFFFFF`（卡片） |
| 主色（國泰綠） | `#00703C` |
| 淡綠（hover / 選中背景） | `#E8F5EE` |
| 邊線色 | `#E0EDE6` |
| 文字主色 | `#1A1A1A` |
| 文字次色 | `#888888` |
| 漲色 | `#00703C` |
| 跌色 | `#D32F2F` |
| 字型 | `'Noto Sans TC', 'Microsoft JhengHei', sans-serif` |

KPI 卡片：白底、左側 3px 綠色實線、`1px solid #E0EDE6` 外框。
導覽列：白底、底部 `3px solid #00703C`。

---

## 頁面結構

```
┌─────────────────────────────────────────────────────┐
│ Nav: 國泰證券 ｜ 概念股監控系統         [搜尋] [即時] │
├─────────────────────────────────────────────────────┤
│ KPI × 5：主題數 | 個股數 | 文章數 | 均漲跌 | 已篩選  │
├──────────────────────┬──────────────────────────────┤
│   主題熱度排行圖      │   熱度 × 漲跌幅散點圖         │
│   (Bar, 可點擊)       │   (Scatter, 聯動高亮)         │
├──────────────────────┴──────────────────────────────┤
│   個股主題明細表（Dash DataTable，聯動篩選）           │
└─────────────────────────────────────────────────────┘
```

---

## Feature A：跨圖表聯動篩選

### 狀態管理

使用 `dcc.Store(id='selected-topic')` 儲存目前選中的主題名稱（`None` 表示未篩選）。

### 互動行為

| 使用者動作 | 結果 |
|---|---|
| 點擊熱度排行中的某一列 | `selected-topic` 更新為該主題 |
| 再次點擊同一列（或點空白） | `selected-topic` 清空為 `None` |
| 點擊散點圖中的某個泡泡 | `selected-topic` 更新為該泡泡的主題 |

### Callback 輸出

`selected-topic` 改變時，同時觸發三個更新：

1. **熱度排行圖**：選中列保持全色，其他列 `opacity=0.25`；選中列加左側綠色標記
2. **散點圖**：選中泡泡放大（`marker.size × 1.5`）並加白色描邊，其他泡泡 `opacity=0.2`
3. **個股表格**：篩選只顯示 `label_fine == selected-topic` 的列；導覽列顯示「已篩選：{主題名稱} ×」徽章

### Callback 簽名（草稿）

```python
@app.callback(
    Output('selected-topic', 'data'),
    Input('heat-chart', 'clickData'),
    Input('scatter-chart', 'clickData'),
    State('selected-topic', 'data'),
)
def update_selected_topic(heat_click, scatter_click, current):
    ...

@app.callback(
    Output('heat-chart', 'figure'),
    Output('scatter-chart', 'figure'),
    Output('stock-table', 'data'),
    Output('filter-badge', 'children'),
    Input('selected-topic', 'data'),
)
def sync_charts(selected_topic):
    ...
```

---

## 資料流

```
result_all.csv  ──┐
                  ├─▶ load_articles()  ─▶ df_articles (全域快取)
tw_stock_list.sqlite3 ─▶ load_prices() ─▶ df_prices  (全域快取)
                  │
                  ├─▶ compute_topic_heat()   ─▶ topic_heat
                  ├─▶ compute_topic_price()  ─▶ topic_stats
                  └─▶ compute_stock_stats()  ─▶ stock_stats
                                                    │
                                              Callback 接收
                                              selected-topic
                                              重新 filter / recolor
```

資料在應用啟動時載入一次並快取，Callback 只做 filter / 顏色調整，不重算原始資料。

---

## 檔案異動範圍

| 檔案 | 變更 |
|---|---|
| `dashboard.py` | 完整改寫：移除 `build_dashboard()` HTML 模板，改為 Dash `app.layout` + Callbacks |
| `requirements.txt` | 新增 `dash>=2.16` |
| 其他（`filter.py`, `topic_model.py`） | 不動 |

---

## 未來功能（本次不實作）

- **B** — 主題熱度時間軸（週折線圖）
- **C** — 個股快速預覽側邊欄
- **D** — 導覽列搜尋 + 快速篩選
- **E** — 轉型股複合分數排行榜

每個功能都可以接在 `selected-topic` 這個 Store 上繼續擴充。
