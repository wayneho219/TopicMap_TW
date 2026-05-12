# Wiki Schema

此文件是本 wiki 的設定檔，記錄慣例、頁面類型、標籤分類法及工作流程客製。LLM 進入 wiki 時會先讀此文件，其慣例覆蓋 `llm-wiki` 技能的預設值。

本文件**與使用者共同演進**。當 LLM 注意到反覆出現的編輯模式或回饋時，會提議新增至此。不再適用的部分請直接刪除。

## Wiki 位置

- Wiki 根目錄：`wiki/`
- 原始來源：`raw/`
- 圖片/資產儲存：`raw/assets/`

## 頁面類型

本 wiki 使用以下頁面類型，各有專屬子目錄：

- `source`（`wiki/sources/`）— 每個來源一頁摘要。
- `entity`（`wiki/entities/`）— 特定事物頁面：股票、公司、資料集、模型、工具。
- `concept`（`wiki/concepts/`）— 概念頁面：方法、演算法、市場主題、供應鏈概念。
- `synthesis`（`wiki/synthesis/`）— 跨主題分析、比較、已歸檔的查詢結果。

## 領域標籤分類

- `taiwan-stock` — 台灣股市相關頁面。
- `nlp` — 自然語言處理方法或工具。
- `topic-modeling` — 主題建模相關內容。
- `supply-chain` — 供應鏈概念或分組。
- `concept-stock` — 概念股分組（如 AI 伺服器、電動車）。
- `rss` — 新聞 RSS 來源相關。
- `sentiment` — 情緒分析相關。
- `pipeline` — 資料處理管線架構。
- `open-question` — 尚未解決的問題。
- `contested` — 來源互相矛盾的頁面。

## 頁面大小

- 軟上限：400 行 / ~2,000 字。超過請考慮拆分。
- 硬上限：800 行。必須拆分。

## Frontmatter 必填欄位

每頁必須包含：
- `type`
- `title`
- `tags`
- `created`
- `updated`

依類型追加：
- `source` 頁面：`authors`、`url`（如適用）、`raw`、`ingested`
- 非 source 頁面：`sources`（列出引用的來源摘要頁）

## 索引結構

目前為平面索引：單一 `wiki/index.md` 列出所有頁面。

當 wiki 超過 ~150 頁或 `index.md` 超過 300 行時，拆分為 `wiki/indexes/<type>.md`。

## 工作流程客製

（初始為空。當與預設 ingest/query/lint 工作流程有差異時，記錄於此。）

## 使用者偏好

- 與使用者溝通和撰寫頁面內容一律使用**繁體中文**。

## Lint 頻率

- 結構性 lint：每 5 次 ingest 後。
- 語意 lint：每週或每 20 次 ingest 後。
- 缺口發現：每月一次。
