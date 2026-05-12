# Wiki 索引

本 wiki 所有頁面的目錄。每筆條目：頁面的 wikilink 與一行摘要。LLM 在回答查詢時首先讀此文件以識別候選頁面。

保持摘要簡潔——每筆一行。索引設計為低成本讀取；臃腫的索引會失去其意義。

當此文件超過 ~300 行或 wiki 超過 ~150 頁時，拆分為 `wiki/indexes/<type>.md`。

---

## Sources（來源）

- [[sa-vision]] — SA.md：AI 投資決策室願景，零預算高自動化，整合輿情 × 行情的目標架構
- [[pipeline-current-state]] — 2026-05-05 管線現況：三大斷層、已完成資料盤點、優先待辦
- [[noise-filter-analysis]] — 版規雜訊過濾分析：filter.py 攔截 322 篇，發現 topic model 誤分類問題

## Entities（實體）

- [[topic-labels-v1]] — 主題標籤 v1（2026-05）：25 中層 + 60 細層，含分類觀察與雜訊標記

## Concepts（概念）

- [[eventcorr-pipeline]] — EventCorr 管線架構：資料流、技術棧、快取機制、已知問題

## Synthesis（綜合分析）

（隨查詢結果歸檔逐步填入）
