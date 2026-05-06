# EventCorr 監控儀表板設計文件

**日期：** 2026-05-06  
**作者：** wayneho219  
**狀態：** 待實作

---

## 目標

建立一個手動觸發、輸出靜態 HTML 的概念股監控儀表板，整合 PTT 主題熱度與股價漲跌幅，讓使用者一眼看出哪些概念股群正在發酵。

---

## 資料流

```
result_all.csv          tw_stock_list.sqlite3
   (topic 分配結果)          (股價/成交量日資料)
        ↓                        ↓
   dashboard.py
        ↓
   dashboard.html  ←── python -m webbrowser 自動開啟
```

**輸入檔案：**
- `result_all.csv` — Phase 2 輸出，每篇文章的主題分配
  - 必要欄位：`StockId`, `ArticleCreateTime`, `topic_fine`, `topic_medium`
- `tw_stock_list.sqlite3` — 每支股票日 K 資料
  - JOIN 鍵：股票代碼（對應 `StockId`）

**輸出檔案：**
- `dashboard.html` — 單一自含 HTML，所有資料嵌入 Plotly JSON

**執行方式：**
```bash
python dashboard.py
# → 輸出 dashboard.html 並自動開啟瀏覽器
```

---

## 儀表板三個分區

### 區塊一：主題熱度排行

- **圖表類型：** 橫向長條圖（Plotly `go.Bar`, `orientation='h'`）
- **Y 軸：** `topic_fine` 標籤（依篇數排序，最熱在上）
- **X 軸：** 文章篇數
- **顏色：** 依 `topic_medium` 分組（同中層主題同色系）
- **目的：** 一眼看出哪個概念股群討論最熱

### 區塊二：熱度 × 漲跌幅散點圖

- **圖表類型：** Plotly `go.Scatter`，mode='markers'
- **X 軸：** 該主題文章篇數（熱度）
- **Y 軸：** 主題內股票平均漲跌幅（%）
- **點大小：** 該主題涵蓋的股票數
- **Hover：** 主題名稱、涵蓋股票數、平均漲幅、代表性個股
- **目的：** 找「討論熱但股價還沒動」的族群（右下象限機會點）

### 區塊三：個股主題明細表

- **圖表類型：** Plotly `go.Table`
- **欄位：** 股票代碼、股票名稱、topic_fine、topic_medium、文章數、近期漲跌幅（%）
- **排序：** 可點擊欄位標題排序（Plotly 內建）
- **目的：** 從主題下鑽到個股層級

---

## 漲跌幅計算基準

- 區間：`result_all.csv` 中 `ArticleCreateTime` 最早日期到最新日期
- 計算方式：`(最後收盤價 - 起始收盤價) / 起始收盤價 × 100`
- 若某股票在該區間無價格資料，散點圖跳過該主題，表格標示「無資料」

---

## 技術棧

| 用途 | 套件 |
|------|------|
| 讀 SQLite | `sqlite3`（標準庫） |
| 資料處理 | `pandas` |
| 圖表生成 | `plotly` |
| 輸出 HTML | `plotly.io.write_html()` |
| 開啟瀏覽器 | `webbrowser`（標準庫） |

全部為專案現有依賴，不需新增套件。

---

## 錯誤處理（系統邊界）

| 情況 | 處理方式 |
|------|------|
| `result_all.csv` 不存在 | 印出提示「請先執行 Phase 2」，sys.exit(1) |
| `tw_stock_list.sqlite3` 不存在 | 印出提示，sys.exit(1) |
| 某主題無對應股價資料 | 熱度排行仍顯示；散點圖跳過；表格標示「無資料」 |

**不處理：** `result_all.csv` 欄位格式異常（信任 Phase 2 管線輸出）。

---

## 範疇外（未來可疊加）

- 時間窗口參數（`--days 7/30/90`）
- 自動排程更新
- RSS 新聞資料整合
