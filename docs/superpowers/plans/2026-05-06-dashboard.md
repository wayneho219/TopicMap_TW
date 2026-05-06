# Dashboard 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 `dashboard.py`，讀取 `result_all.csv` + `data/tw_stock_list.sqlite3`，輸出並自動開啟 `dashboard.html` 靜態監控儀表板。

**Architecture:** 單一腳本，純函式設計。資料層（load/compute）與視覺層（chart builders）分離，`main()` 串接。所有資料預先計算後嵌入 Plotly HTML，瀏覽器無需 server。

**Tech Stack:** `pandas`, `plotly`, `sqlite3`（標準庫）, `webbrowser`（標準庫）, `pytest`

---

## 欄位對照

| 來源 | 欄位 | 說明 |
|------|------|------|
| `result_all.csv` | `stock_id` (int) | 股票代碼 |
| `result_all.csv` | `label_fine` (str) | 細層主題標籤 |
| `result_all.csv` | `label_medium` (str) | 中層主題標籤 |
| `result_all.csv` | `ArticleCreateTime` (str) | 文章日期 |
| `tw_stock_list` | `stock_code` (str) | 股票代碼（JOIN 鍵，需 `str(stock_id)`） |
| `tw_stock_list` | `stock_name` (str) | 股票名稱 |
| `tw_stock_list` | `change_pct` (str) | 當日漲跌幅，如 `"+1.20%"` |
| `tw_stock_list` | `quote_date` (str) | 報價日期（取最新日） |

---

## 檔案結構

```
dashboard.py           ← 主腳本（資料層 + 視覺層 + main）
tests/
  test_dashboard.py    ← 資料層單元測試
dashboard.html         ← 輸出（generated，不 commit）
```

---

## Task 1：專案骨架與測試環境

**Files:**
- Create: `dashboard.py`
- Create: `tests/__init__.py`
- Create: `tests/test_dashboard.py`

- [ ] **Step 1: 建立 tests/ 目錄與空白 __init__.py**

```bash
mkdir -p tests && touch tests/__init__.py
```

- [ ] **Step 2: 建立 dashboard.py 骨架**

```python
# dashboard.py
import sys
import sqlite3
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

ARTICLES_PATH = "result_all.csv"
DB_PATH = "data/tw_stock_list.sqlite3"
OUTPUT_PATH = "dashboard.html"


def load_articles(path: str = ARTICLES_PATH) -> pd.DataFrame:
    raise NotImplementedError


def load_prices(db_path: str = DB_PATH) -> pd.DataFrame:
    raise NotImplementedError


def compute_topic_heat(articles: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def build_heat_chart(topic_heat: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_scatter_chart(topic_stats: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_table_chart(stock_stats: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_dashboard(heat_fig: go.Figure, scatter_fig: go.Figure, table_fig: go.Figure) -> str:
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 確認 pytest 可執行（目前無測試）**

```bash
python3 -m pytest tests/ -v
```

Expected: `no tests ran` 或 `0 passed`，無 ImportError。

- [ ] **Step 4: Commit**

```bash
git add dashboard.py tests/__init__.py tests/test_dashboard.py
git commit -m "chore: scaffold dashboard.py and test structure"
```

---

## Task 2：load_articles()

**Files:**
- Modify: `dashboard.py`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_dashboard.py
import pytest
import pandas as pd
import io
from dashboard import load_articles

SAMPLE_CSV = """stock_id,industry_name,ArticleCreateTime,label_medium,label_fine
1101,水泥工業,2026-03-12,合併財務報告公告,季合併財報公告
1101,水泥工業,2026-03-11,合併財務報告公告,季合併財報公告
2330,半導體,2026-03-10,AI科技概念股,AI液冷記憶體個股
"""

def test_load_articles_columns(tmp_path):
    f = tmp_path / "articles.csv"
    f.write_text(SAMPLE_CSV)
    df = load_articles(str(f))
    assert set(["stock_id", "label_fine", "label_medium", "ArticleCreateTime"]).issubset(df.columns)

def test_load_articles_stock_id_is_str(tmp_path):
    f = tmp_path / "articles.csv"
    f.write_text(SAMPLE_CSV)
    df = load_articles(str(f))
    assert df["stock_id"].dtype == object  # string type for JOIN

def test_load_articles_missing_file():
    with pytest.raises(SystemExit):
        load_articles("nonexistent.csv")
```

- [ ] **Step 2: 執行確認失敗**

```bash
python3 -m pytest tests/test_dashboard.py::test_load_articles_columns -v
```

Expected: FAILED（NotImplementedError）

- [ ] **Step 3: 實作 load_articles()**

```python
def load_articles(path: str = ARTICLES_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        print(f"[錯誤] 找不到 {path}，請先執行 Phase 2 產生 result_all.csv")
        sys.exit(1)
    df = pd.read_csv(path)
    df["stock_id"] = df["stock_id"].astype(str)
    return df
```

- [ ] **Step 4: 執行確認通過**

```bash
python3 -m pytest tests/test_dashboard.py -k "load_articles" -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat: implement load_articles with validation"
```

---

## Task 3：load_prices()

**Files:**
- Modify: `dashboard.py`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: 寫失敗測試**

```python
# append to tests/test_dashboard.py
import sqlite3
from dashboard import load_prices

def test_load_prices_columns(tmp_path):
    db = tmp_path / "tw_stock_list.sqlite3"
    conn = sqlite3.connect(str(db))
    conn.execute("""
        CREATE TABLE tw_stock_list (
            stock_code TEXT, stock_name TEXT, change_pct TEXT, quote_date TEXT
        )
    """)
    conn.execute("INSERT INTO tw_stock_list VALUES ('1101','台泥','+1.20%','2026-04-13')")
    conn.execute("INSERT INTO tw_stock_list VALUES ('2330','台積電','-0.50%','2026-04-13')")
    conn.commit(); conn.close()
    df = load_prices(str(db))
    assert set(["stock_code", "stock_name", "change_pct_float"]).issubset(df.columns)

def test_load_prices_change_pct_is_float(tmp_path):
    db = tmp_path / "tw_stock_list.sqlite3"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE tw_stock_list (stock_code TEXT, stock_name TEXT, change_pct TEXT, quote_date TEXT)")
    conn.execute("INSERT INTO tw_stock_list VALUES ('1101','台泥','+1.20%','2026-04-13')")
    conn.commit(); conn.close()
    df = load_prices(str(db))
    assert df["change_pct_float"].dtype == float
    assert abs(df.iloc[0]["change_pct_float"] - 1.20) < 0.01

def test_load_prices_missing_db():
    with pytest.raises(SystemExit):
        load_prices("nonexistent.sqlite3")
```

- [ ] **Step 2: 執行確認失敗**

```bash
python3 -m pytest tests/test_dashboard.py -k "load_prices" -v
```

Expected: FAILED（NotImplementedError）

- [ ] **Step 3: 實作 load_prices()**

```python
def load_prices(db_path: str = DB_PATH) -> pd.DataFrame:
    if not Path(db_path).exists():
        print(f"[錯誤] 找不到 {db_path}，請確認資料庫路徑")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(
        "SELECT stock_code, stock_name, change_pct, quote_date "
        "FROM tw_stock_list WHERE quote_date IS NOT NULL",
        conn,
    )
    conn.close()
    # 取最新日期快照
    latest = df["quote_date"].max()
    df = df[df["quote_date"] == latest].copy()
    # 解析 "+1.20%" → 1.20
    df["change_pct_float"] = (
        df["change_pct"].str.replace("%", "", regex=False).astype(float)
    )
    return df
```

- [ ] **Step 4: 執行確認通過**

```bash
python3 -m pytest tests/test_dashboard.py -k "load_prices" -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat: implement load_prices with change_pct parsing"
```

---

## Task 4：compute_topic_heat() 與 compute_topic_price()

**Files:**
- Modify: `dashboard.py`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: 寫失敗測試**

```python
# append to tests/test_dashboard.py
from dashboard import compute_topic_heat, compute_topic_price

def _sample_articles():
    return pd.DataFrame({
        "stock_id": ["1101", "1101", "2330", "2330", "2330"],
        "label_fine": ["AI液冷", "AI液冷", "AI液冷", "航運指數", "航運指數"],
        "label_medium": ["AI科技", "AI科技", "AI科技", "航運", "航運"],
        "ArticleCreateTime": ["2026-03-10"] * 5,
    })

def _sample_prices():
    return pd.DataFrame({
        "stock_code": ["1101", "2330"],
        "stock_name": ["台泥", "台積電"],
        "change_pct_float": [1.20, -0.50],
    })

def test_compute_topic_heat_counts():
    heat = compute_topic_heat(_sample_articles())
    assert set(["label_fine", "label_medium", "article_count"]).issubset(heat.columns)
    ai_row = heat[heat["label_fine"] == "AI液冷"].iloc[0]
    assert ai_row["article_count"] == 3

def test_compute_topic_heat_sorted():
    heat = compute_topic_heat(_sample_articles())
    assert heat.iloc[0]["article_count"] >= heat.iloc[1]["article_count"]

def test_compute_topic_price_avg():
    stats = compute_topic_price(_sample_articles(), _sample_prices())
    assert set(["label_fine", "label_medium", "article_count", "avg_change_pct", "stock_count"]).issubset(stats.columns)
    ai_row = stats[stats["label_fine"] == "AI液冷"].iloc[0]
    # 1101(+1.20) 和 2330(-0.50) 都在 AI液冷 → avg = (1.20 + (-0.50)) / 2 = 0.35
    assert abs(ai_row["avg_change_pct"] - 0.35) < 0.01

def test_compute_topic_price_excludes_no_price():
    articles = _sample_articles()
    prices = pd.DataFrame({  # 只有 1101
        "stock_code": ["1101"], "stock_name": ["台泥"], "change_pct_float": [1.20]
    })
    stats = compute_topic_price(articles, prices)
    # 航運指數只有 2330，2330 無價格資料 → 應被排除
    assert "航運指數" not in stats["label_fine"].values
```

- [ ] **Step 2: 執行確認失敗**

```bash
python3 -m pytest tests/test_dashboard.py -k "compute_topic" -v
```

Expected: FAILED（NotImplementedError）

- [ ] **Step 3: 實作 compute_topic_heat()**

```python
def compute_topic_heat(articles: pd.DataFrame) -> pd.DataFrame:
    heat = (
        articles.groupby(["label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
        .sort_values("article_count", ascending=False)
    )
    return heat
```

- [ ] **Step 4: 實作 compute_topic_price()**

```python
def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    merged = articles.merge(prices[["stock_code", "change_pct_float"]],
                            left_on="stock_id", right_on="stock_code", how="inner")
    # 每支股票在每個主題只算一次（per-stock 平均，不受文章數影響）
    deduped = merged.drop_duplicates(subset=["stock_id", "label_fine"])
    heat = compute_topic_heat(articles)
    stats = (
        deduped.groupby(["label_fine", "label_medium"])
        .agg(
            avg_change_pct=("change_pct_float", "mean"),
            stock_count=("stock_id", "nunique"),
        )
        .reset_index()
    )
    stats = stats.merge(heat, on=["label_fine", "label_medium"], how="left")
    return stats
```

- [ ] **Step 5: 執行確認通過**

```bash
python3 -m pytest tests/test_dashboard.py -k "compute_topic" -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat: implement compute_topic_heat and compute_topic_price"
```

---

## Task 5：compute_stock_stats()

**Files:**
- Modify: `dashboard.py`
- Modify: `tests/test_dashboard.py`

- [ ] **Step 1: 寫失敗測試**

```python
# append to tests/test_dashboard.py
from dashboard import compute_stock_stats

def test_compute_stock_stats_columns():
    stats = compute_stock_stats(_sample_articles(), _sample_prices())
    assert set(["stock_id", "stock_name", "label_fine", "label_medium", 
                "article_count", "change_pct_float"]).issubset(stats.columns)

def test_compute_stock_stats_primary_topic():
    # 1101 在 AI液冷(2篇)，所以主要主題應該是 AI液冷
    stats = compute_stock_stats(_sample_articles(), _sample_prices())
    row_1101 = stats[stats["stock_id"] == "1101"].iloc[0]
    assert row_1101["label_fine"] == "AI液冷"
    assert row_1101["article_count"] == 2
```

- [ ] **Step 2: 執行確認失敗**

```bash
python3 -m pytest tests/test_dashboard.py -k "compute_stock_stats" -v
```

Expected: FAILED（NotImplementedError）

- [ ] **Step 3: 實作 compute_stock_stats()**

```python
def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    # 每個 (stock_id, label_fine) 的文章數
    counts = (
        articles.groupby(["stock_id", "label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
    )
    # 取每支股票文章數最多的主題（主要主題）
    idx = counts.groupby("stock_id")["article_count"].idxmax()
    primary = counts.loc[idx].reset_index(drop=True)
    # JOIN 股價
    result = primary.merge(
        prices[["stock_code", "stock_name", "change_pct_float"]],
        left_on="stock_id", right_on="stock_code", how="inner"
    ).drop(columns=["stock_code"])
    return result.sort_values("article_count", ascending=False)
```

- [ ] **Step 4: 執行確認通過**

```bash
python3 -m pytest tests/test_dashboard.py -k "compute_stock_stats" -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add dashboard.py tests/test_dashboard.py
git commit -m "feat: implement compute_stock_stats with primary topic selection"
```

---

## Task 6：Chart builders 與 main()

**Files:**
- Modify: `dashboard.py`

（圖表輸出為視覺結果，不做 Plotly 圖表的單元測試，改用 smoke test 驗證執行不報錯。）

- [ ] **Step 1: 實作 build_heat_chart()**

```python
def build_heat_chart(topic_heat: pd.DataFrame) -> go.Figure:
    # 顏色對應 label_medium
    medium_labels = topic_heat["label_medium"].unique().tolist()
    color_map = {m: f"hsl({i * 360 // len(medium_labels)}, 60%, 55%)" 
                 for i, m in enumerate(medium_labels)}
    colors = topic_heat["label_medium"].map(color_map)

    fig = go.Figure(go.Bar(
        x=topic_heat["article_count"],
        y=topic_heat["label_fine"],
        orientation="h",
        marker_color=colors,
        text=topic_heat["article_count"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>篇數：%{x}<extra></extra>",
    ))
    fig.update_layout(
        title="主題熱度排行",
        xaxis_title="文章篇數",
        yaxis={"categoryorder": "total ascending"},
        height=max(400, len(topic_heat) * 22),
        margin={"l": 200},
    )
    return fig
```

- [ ] **Step 2: 實作 build_scatter_chart()**

```python
def build_scatter_chart(topic_stats: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=topic_stats["article_count"],
        y=topic_stats["avg_change_pct"],
        mode="markers+text",
        text=topic_stats["label_fine"],
        textposition="top center",
        marker={
            "size": topic_stats["stock_count"].clip(upper=50) + 5,
            "color": topic_stats["avg_change_pct"],
            "colorscale": "RdYlGn",
            "showscale": True,
            "colorbar": {"title": "均漲跌%"},
        },
        hovertemplate=(
            "<b>%{text}</b><br>"
            "熱度：%{x} 篇<br>"
            "均漲跌：%{y:.2f}%<br>"
            "涵蓋股票：%{marker.size}<extra></extra>"
        ),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        title="主題熱度 × 股價漲跌幅",
        xaxis_title="文章篇數（熱度）",
        yaxis_title="主題均漲跌幅 (%)",
        height=500,
    )
    return fig
```

- [ ] **Step 3: 實作 build_table_chart()**

```python
def build_table_chart(stock_stats: pd.DataFrame) -> go.Figure:
    pct_display = stock_stats["change_pct_float"].apply(
        lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
    )
    fig = go.Figure(go.Table(
        header={
            "values": ["股票代碼", "股票名稱", "細層主題", "中層主題", "文章數", "漲跌幅"],
            "fill_color": "#2c3e50",
            "font": {"color": "white", "size": 13},
            "align": "center",
        },
        cells={
            "values": [
                stock_stats["stock_id"],
                stock_stats["stock_name"],
                stock_stats["label_fine"],
                stock_stats["label_medium"],
                stock_stats["article_count"],
                pct_display,
            ],
            "fill_color": [
                ["#f5f5f5" if i % 2 == 0 else "white" for i in range(len(stock_stats))]
            ],
            "align": ["center", "left", "left", "left", "center", "center"],
        },
    ))
    fig.update_layout(title="個股主題明細", height=500)
    return fig
```

- [ ] **Step 4: 實作 build_dashboard()**

```python
def build_dashboard(heat_fig: go.Figure, scatter_fig: go.Figure, table_fig: go.Figure) -> str:
    html_parts = []
    for fig in [heat_fig, scatter_fig, table_fig]:
        html_parts.append(
            pio.to_html(fig, include_plotlyjs="cdn" if not html_parts else False,
                        full_html=False)
        )
    body = "\n".join(html_parts)
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<title>EventCorr 概念股監控儀表板</title>
<style>
  body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
  h1 {{ color: #2c3e50; }}
  .chart {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
<h1>EventCorr 概念股監控儀表板</h1>
<div class="chart">{html_parts[0]}</div>
<div class="chart">{html_parts[1]}</div>
<div class="chart">{html_parts[2]}</div>
</body>
</html>"""
```

- [ ] **Step 5: 實作 main()**

```python
def main():
    articles = load_articles()
    prices = load_prices()

    topic_heat = compute_topic_heat(articles)
    topic_stats = compute_topic_price(articles, prices)
    stock_stats = compute_stock_stats(articles, prices)

    heat_fig = build_heat_chart(topic_heat)
    scatter_fig = build_scatter_chart(topic_stats)
    table_fig = build_table_chart(stock_stats)

    html = build_dashboard(heat_fig, scatter_fig, table_fig)
    Path(OUTPUT_PATH).write_text(html, encoding="utf-8")
    print(f"[完成] 輸出：{OUTPUT_PATH}")
    webbrowser.open(f"file://{Path(OUTPUT_PATH).resolve()}")
```

- [ ] **Step 6: Smoke test — 全部測試通過**

```bash
python3 -m pytest tests/ -v
```

Expected: 全部 passed，無 NotImplementedError

- [ ] **Step 7: 實際執行驗證**

```bash
python3 dashboard.py
```

Expected:
- 印出 `[完成] 輸出：dashboard.html`
- 瀏覽器自動開啟，顯示三個分區

- [ ] **Step 8: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement chart builders and main() for dashboard"
```

---

## Task 7：收尾與文件

**Files:**
- Modify: `CLAUDE.md`（新增 dashboard 執行說明）
- Modify: `wiki/log.md`（記錄 ingest）

- [ ] **Step 1: 在 CLAUDE.md 新增 dashboard 段落**

在 `## Running the Pipeline` 下加入：

```markdown
### Dashboard (`dashboard.py`)

先完成 Phase 2，再執行：
```bash
python dashboard.py
```

輸出 `dashboard.html`（自動開啟瀏覽器）。包含：主題熱度排行、熱度×漲跌幅散點、個股明細表。
```

- [ ] **Step 2: 將 dashboard 設計記入 wiki/log.md**

在 `wiki/log.md` 末尾附加：

```
## [2026-05-06] ingest | dashboard.py 設計完成 → docs/superpowers/specs/2026-05-06-dashboard-design.md
```

- [ ] **Step 3: 最終 commit**

```bash
git add CLAUDE.md wiki/log.md docs/
git commit -m "docs: add dashboard usage to CLAUDE.md and wiki log"
```
