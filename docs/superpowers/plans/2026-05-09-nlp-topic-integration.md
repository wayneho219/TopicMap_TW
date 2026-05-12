# NLP 主題分類整合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 daniel-dev 的 NLP 主題分類資料（invested_amount）存入現有 SQLite，並在前端 MarketPage 的「類股」tab 中以 accordion 形式展示「主題」。

**Architecture:** `topic_model.py` Phase 2 新增 yfinance 股價抓取後輸出 `output/result_all.csv`（含 invested_amount）；`scripts/import_nlp_topics.py` 將 CSV 匯入 `tw_stock_list.sqlite3` 的兩張新表；後端新增 3 個 `/api/topics` 端點；前端在現有 SectorTab 加 toggle，展示 medium→fine accordion + TopicDetailPage。

**Tech Stack:** Python / pandas / sqlite3 / yfinance；FastAPI / pytest / TestClient；React / TypeScript / Vite / Tailwind / react-router-dom

---

## File Map

| 動作 | 路徑 | 說明 |
|------|------|------|
| Modify | `rss_scraper.py` | 新增 STOPWORDS 清單 |
| Modify | `topic_model.py` | 新增 yfinance 股價段落、擴充 result_all.csv 欄位、新增 invested_amount_*.csv |
| Create | `scripts/import_nlp_topics.py` | CSV → SQLite 匯入（冪等） |
| Create | `tests/test_import_nlp_topics.py` | import script 單元測試 |
| Create | `tests/test_topics_api.py` | API 端點測試 |
| Modify | `backend/main.py` | 新增 3 個 /api/topics 端點 |
| Create | `frontend/src/hooks/useTopics.ts` | 主題相關 API hooks |
| Create | `frontend/src/components/TopicTab.tsx` | accordion 主題列表 |
| Modify | `frontend/src/pages/MarketPage.tsx` | SectorTab 加類股/主題 toggle |
| Create | `frontend/src/pages/TopicDetailPage.tsx` | 主題個股列表頁 |
| Modify | `frontend/src/App.tsx` | 新增 /topic/:level/:name 路由 |

---

## Task 1：合併 rss_scraper.py STOPWORDS

**Files:**
- Modify: `rss_scraper.py`

- [ ] **Step 1：在 `MAX_PER_STOCK = 10` 之後插入 STOPWORDS**

開啟 `rss_scraper.py`，找到 `MAX_PER_STOCK = 10` 這行，在其後插入：

```python
STOPWORDS = [
    # 法人買賣超
    "買超", "賣超", "外資", "投信", "自營商", "排行", "張數", "收盤價", "漲跌", "百萬",
    # 月營收公告
    "去年同期", "累計", "增減", "本月", "去年", "營收", "收入", "百分比", "自結",
    # 財報公告
    "每股盈餘", "EPS", "稅前", "稅後", "淨利", "損益", "現金股利",
    # 公告垃圾
    "公開資訊觀測站", "MOPS", "TWSE", "證交所", "櫃買中心", "重大訊息", "公告",
    # 注意股
    "注意交易資訊", "有價證券", "達公布標準",
    # 股票抽籤
    "申購", "承銷", "承銷價", "扣款日", "抽籤日", "進場", "退場",
]
```

- [ ] **Step 2：確認語法無誤**

```bash
python -c "import rss_scraper; print('OK')"
```

Expected: `OK`

- [ ] **Step 3：Commit**

```bash
git add rss_scraper.py
git commit -m "feat(scraper): add STOPWORDS filter for noise signals"
```

---

## Task 2：合併 topic_model.py — yfinance + invested_amount

**Files:**
- Modify: `topic_model.py`

- [ ] **Step 1：在頂部 import 區塊加入 yfinance**

找到 `topic_model.py` 的 import 區塊（約第 31-42 行），在最後一個 import 之後加入：

```python
import yfinance as yf
```

- [ ] **Step 2：在 topics_*.csv 輸出之後、result_all.csv 輸出之前插入股價抓取段落**

找到以下這段（約第 307-311 行）：
```python
    # ── 完整結果 ─────────────────────────────────────────────────────────────
    out_cols = ["stock_id", "industry_name", "ArticleCreateTime",
                "label_medium", "label_fine"]
    df[out_cols].to_csv("output/result_all.csv", encoding="utf-8-sig", index=False)
    print("  output/result_all.csv")
```

將整段替換為：

```python
    # ── 股價與投入金額（yfinance）────────────────────────────────────────────
    print("\n  正在抓取股票歷史股價（yfinance）...")
    df["close_price"] = None
    df["volume"] = None
    df["invested_amount"] = None

    _stock_cache: dict[str, "pd.DataFrame"] = {}
    for sid in df["stock_id"].unique():
        try:
            ticker = f"{str(sid).zfill(4)}.TW"
            hist = yf.Ticker(ticker).history(period="2y")
            if not hist.empty:
                _stock_cache[str(sid)] = hist
        except Exception:
            pass

    for idx, row in df.iterrows():
        sid = str(row["stock_id"])
        art_date = pd.to_datetime(row["ArticleCreateTime"]).date()
        if sid not in _stock_cache:
            continue
        hist = _stock_cache[sid]
        valid = hist.index[hist.index.notna()]
        matching = valid[valid.to_series().dt.date <= art_date]
        if len(matching) == 0:
            continue
        closest = matching[-1]
        cp = float(hist.loc[closest, "Close"])
        vol = int(hist.loc[closest, "Volume"])
        df.at[idx, "close_price"] = cp
        df.at[idx, "volume"] = vol
        df.at[idx, "invested_amount"] = cp * vol

    # ── 完整結果 ─────────────────────────────────────────────────────────────
    out_cols = ["stock_id", "industry_name", "ArticleCreateTime",
                "close_price", "volume", "invested_amount",
                "label_medium", "label_fine"]
    df[out_cols].to_csv("output/result_all.csv", encoding="utf-8-sig", index=False)
    print("  output/result_all.csv")

    # ── 各層主題投入金額統計 CSV ──────────────────────────────────────────────
    for level in ["medium", "fine"]:
        inv_stat = (
            df.groupby(f"label_{level}")["invested_amount"].sum()
            .fillna(0)
            .sort_values(ascending=False)
            .to_frame("總投入金額")
        )
        inv_stat.index.name = f"主題({level})"
        inv_stat.to_csv(f"output/invested_amount_{level}.csv", encoding="utf-8-sig")
        print(f"  output/invested_amount_{level}.csv")
```

- [ ] **Step 3：確認語法無誤**

```bash
python -c "
import ast, sys
with open('topic_model.py') as f:
    src = f.read()
ast.parse(src)
print('syntax OK')
"
```

Expected: `syntax OK`

- [ ] **Step 4：Commit**

```bash
git add topic_model.py
git commit -m "feat(pipeline): add yfinance price fetch and invested_amount to topic_model Phase 2"
```

---

## Task 3：準備 output/result_all.csv

topic_model.py 需要完整跑 Phase 2 才能產出含 invested_amount 的 result_all.csv。  
若目前 `output/result_all.csv` 不含 `close_price` 欄位，需從 daniel-dev 取得或重跑 pipeline。

**Files:**（無程式碼異動）

- [ ] **Step 1：確認現有 result_all.csv 是否含 close_price**

```bash
head -1 output/result_all.csv
```

若輸出不含 `close_price`，執行 Step 2；否則跳至 Task 4。

- [ ] **Step 2：從 daniel-dev 提取含 close_price 的 result_all.csv**

```bash
mkdir -p output
git show origin/daniel-dev:result_all.csv > output/result_all.csv
```

- [ ] **Step 3：確認欄位正確**

```bash
head -2 output/result_all.csv
```

Expected 第一行包含：`stock_id,industry_name,ArticleCreateTime,close_price,volume,invested_amount,label_medium,label_fine`

---

## Task 4：撰寫 import script 測試

**Files:**
- Create: `tests/test_import_nlp_topics.py`

- [ ] **Step 1：建立測試檔**

```python
# tests/test_import_nlp_topics.py
import os
import sqlite3
import textwrap
import pytest

# 讓 pytest 能 import scripts 目錄
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.import_nlp_topics import import_nlp_topics

CSV_CONTENT = textwrap.dedent("""\
    stock_id,industry_name,ArticleCreateTime,close_price,volume,invested_amount,label_medium,label_fine
    2330,半導體業,2026-03-05,1000.0,42000000,42000000000.0,AI半導體,台積電股
    2330,半導體業,2026-03-07,1020.0,38000000,38760000000.0,AI半導體,台積電股
    2454,半導體業,2026-03-05,820.0,5000000,4100000000.0,AI半導體,消費電子
    1101,水泥工業,2026-03-05,25.5,8000000,204000000.0,高股息,年度配息
""")

@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "result_all.csv"
    p.write_text(CSV_CONTENT, encoding="utf-8")
    return str(p)

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.sqlite3")

def test_creates_medium_topics(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT name FROM nlp_topics WHERE level='medium' ORDER BY name"
    ).fetchall()
    conn.close()
    assert [r[0] for r in rows] == ["AI半導體", "高股息"]

def test_creates_fine_topics_with_correct_parent(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT f.name, m.name AS parent_name
        FROM nlp_topics f
        JOIN nlp_topics m ON m.id = f.parent_id
        WHERE f.level = 'fine'
        ORDER BY f.name
    """).fetchall()
    conn.close()
    name_to_parent = {r[0]: r[1] for r in rows}
    assert name_to_parent["台積電股"] == "AI半導體"
    assert name_to_parent["消費電子"] == "AI半導體"
    assert name_to_parent["年度配息"] == "高股息"

def test_medium_total_invested(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT total_invested FROM nlp_topics WHERE name='AI半導體' AND level='medium'"
    ).fetchone()
    conn.close()
    # 42B + 38.76B + 4.1B = 84,860,000,000
    assert abs(row[0] - 84_860_000_000.0) < 1.0

def test_topic_stocks_populated(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM nlp_topic_stocks").fetchone()[0]
    conn.close()
    assert count > 0

def test_fine_stock_invested(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT ts.total_invested
        FROM nlp_topic_stocks ts
        JOIN nlp_topics t ON t.id = ts.topic_id
        WHERE t.name = '台積電股' AND t.level = 'fine' AND ts.stock_code = '2330'
    """).fetchone()
    conn.close()
    # 42B + 38.76B = 80,760,000,000
    assert abs(row[0] - 80_760_000_000.0) < 1.0

def test_idempotent(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM nlp_topics WHERE level='medium'"
    ).fetchone()[0]
    conn.close()
    assert count == 2
```

- [ ] **Step 2：確認測試因尚無實作而失敗**

```bash
python -m pytest tests/test_import_nlp_topics.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'scripts.import_nlp_topics'`

---

## Task 5：實作 scripts/import_nlp_topics.py

**Files:**
- Create: `scripts/import_nlp_topics.py`

- [ ] **Step 1：建立 scripts/__init__.py（若不存在）**

```bash
touch scripts/__init__.py
```

- [ ] **Step 2：建立 import_nlp_topics.py**

```python
# scripts/import_nlp_topics.py
import os
import sqlite3
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'output', 'result_all.csv')
DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

_DDL = '''
DROP TABLE IF EXISTS nlp_topic_stocks;
DROP TABLE IF EXISTS nlp_topics;

CREATE TABLE nlp_topics (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    level          TEXT    NOT NULL CHECK(level IN ('medium', 'fine')),
    parent_id      INTEGER REFERENCES nlp_topics(id),
    total_invested REAL    NOT NULL DEFAULT 0,
    article_count  INTEGER NOT NULL DEFAULT 0,
    stock_count    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_nlp_topics_level  ON nlp_topics(level);
CREATE INDEX idx_nlp_topics_parent ON nlp_topics(parent_id);

CREATE TABLE nlp_topic_stocks (
    topic_id       INTEGER NOT NULL REFERENCES nlp_topics(id) ON DELETE CASCADE,
    stock_code     TEXT    NOT NULL,
    article_count  INTEGER NOT NULL DEFAULT 0,
    total_invested REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (topic_id, stock_code)
);
CREATE INDEX idx_nlp_topic_stocks_code ON nlp_topic_stocks(stock_code);
'''

def import_nlp_topics(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"result_all.csv not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'stock_id': str})
    df['invested_amount'] = pd.to_numeric(df['invested_amount'], errors='coerce').fillna(0)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_DDL)

        # ── medium 主題 ────────────────────────────────────────────────────────
        med_stats = (
            df.groupby('label_medium')
            .agg(
                total_invested=('invested_amount', 'sum'),
                article_count=('label_medium', 'count'),
                stock_count=('stock_id', 'nunique'),
            )
            .reset_index()
        )
        medium_id: dict[str, int] = {}
        for _, row in med_stats.iterrows():
            cur = conn.execute(
                'INSERT INTO nlp_topics (name, level, parent_id, total_invested, article_count, stock_count) '
                'VALUES (?,?,?,?,?,?)',
                (row['label_medium'], 'medium', None,
                 float(row['total_invested']), int(row['article_count']), int(row['stock_count'])),
            )
            medium_id[row['label_medium']] = cur.lastrowid

        # ── fine 主題 ──────────────────────────────────────────────────────────
        fine_stats = (
            df.groupby(['label_medium', 'label_fine'])
            .agg(
                total_invested=('invested_amount', 'sum'),
                article_count=('label_fine', 'count'),
                stock_count=('stock_id', 'nunique'),
            )
            .reset_index()
        )
        fine_id: dict[tuple, int] = {}
        for _, row in fine_stats.iterrows():
            parent = medium_id[row['label_medium']]
            cur = conn.execute(
                'INSERT INTO nlp_topics (name, level, parent_id, total_invested, article_count, stock_count) '
                'VALUES (?,?,?,?,?,?)',
                (row['label_fine'], 'fine', parent,
                 float(row['total_invested']), int(row['article_count']), int(row['stock_count'])),
            )
            fine_id[(row['label_medium'], row['label_fine'])] = cur.lastrowid

        # ── medium × stock ────────────────────────────────────────────────────
        for med, grp in df.groupby('label_medium'):
            topic_id = medium_id[med]
            for sid, sgrp in grp.groupby('stock_id'):
                conn.execute(
                    'INSERT INTO nlp_topic_stocks (topic_id, stock_code, article_count, total_invested) '
                    'VALUES (?,?,?,?)',
                    (topic_id, str(sid), len(sgrp), float(sgrp['invested_amount'].sum())),
                )

        # ── fine × stock ──────────────────────────────────────────────────────
        for (med, fine), grp in df.groupby(['label_medium', 'label_fine']):
            topic_id = fine_id[(med, fine)]
            for sid, sgrp in grp.groupby('stock_id'):
                conn.execute(
                    'INSERT INTO nlp_topic_stocks (topic_id, stock_code, article_count, total_invested) '
                    'VALUES (?,?,?,?)',
                    (topic_id, str(sid), len(sgrp), float(sgrp['invested_amount'].sum())),
                )

        conn.commit()
        n_med = len(medium_id)
        n_fine = len(fine_id)
        print(f"匯入完成：{n_med} 個 medium 主題，{n_fine} 個 fine 主題")
    finally:
        conn.close()


if __name__ == '__main__':
    import_nlp_topics()
```

- [ ] **Step 3：執行測試，確認全部通過**

```bash
python -m pytest tests/test_import_nlp_topics.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 4：對真實 DB 執行 import**

```bash
python scripts/import_nlp_topics.py
```

Expected:
```
匯入完成：25 個 medium 主題，60 個 fine 主題
```

- [ ] **Step 5：Commit**

```bash
git add scripts/__init__.py scripts/import_nlp_topics.py tests/test_import_nlp_topics.py
git commit -m "feat(db): add NLP topic import script with nlp_topics and nlp_topic_stocks tables"
```

---

## Task 6：撰寫後端 API 測試

**Files:**
- Create: `tests/test_topics_api.py`

- [ ] **Step 1：建立測試檔**

```python
# tests/test_topics_api.py
import os
import sqlite3
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

def _seed(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE nlp_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT NOT NULL,
            parent_id INTEGER,
            total_invested REAL NOT NULL DEFAULT 0,
            article_count INTEGER NOT NULL DEFAULT 0,
            stock_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE nlp_topic_stocks (
            topic_id INTEGER NOT NULL,
            stock_code TEXT NOT NULL,
            article_count INTEGER NOT NULL DEFAULT 0,
            total_invested REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (topic_id, stock_code)
        );
        CREATE TABLE tw_stock_list (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL DEFAULT '',
            industry_code TEXT NOT NULL DEFAULT '',
            industry_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            source_as_of TEXT NOT NULL DEFAULT '',
            synced_at TEXT NOT NULL DEFAULT '',
            close_price REAL,
            change_val TEXT,
            change_pct TEXT,
            volume INTEGER,
            quote_date TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL
        );
        INSERT INTO nlp_topics VALUES (1,'AI半導體','medium',NULL,854467864250.49,187,25);
        INSERT INTO nlp_topics VALUES (2,'高股息','medium',NULL,174688926965.03,160,30);
        INSERT INTO nlp_topics VALUES (3,'台積電股','fine',1,461413362216.5,42,1);
        INSERT INTO nlp_topics VALUES (4,'消費電子','fine',1,344648974867.14,35,8);
        INSERT INTO nlp_topic_stocks VALUES (1,'2330',42,461413362216.5);
        INSERT INTO nlp_topic_stocks VALUES (3,'2330',42,461413362216.5);
        INSERT INTO tw_stock_list(stock_code,stock_name,close_price,change_val,change_pct,volume)
            VALUES ('2330','台積電',1000.0,'+35','+3.50%',42000000);
    ''')
    conn.commit()
    conn.close()

@pytest.fixture
def client(tmp_path):
    db = str(tmp_path / 'test.sqlite3')
    _seed(db)
    import backend.main as m
    original = m.DB_PATH
    m.DB_PATH = db
    yield TestClient(m.app)
    m.DB_PATH = original

def test_get_topics_medium_sorted(client):
    r = client.get('/api/topics?level=medium')
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]['name'] == 'AI半導體'
    assert data[0]['totalInvested'] == pytest.approx(854467864250.49)
    assert data[0]['articleCount'] == 187
    assert data[0]['stockCount'] == 25

def test_get_topics_fine(client):
    r = client.get('/api/topics?level=fine')
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_get_topic_children(client):
    r = client.get('/api/topics/AI半導體/children')
    assert r.status_code == 200
    children = r.json()
    assert len(children) == 2
    assert children[0]['name'] == '台積電股'
    assert children[0]['level'] == 'fine'

def test_get_topic_children_not_found(client):
    r = client.get('/api/topics/不存在主題/children')
    assert r.status_code == 404

def test_get_topic_stocks_heat(client):
    r = client.get('/api/topics/AI半導體/stocks?level=medium&sort=heat')
    assert r.status_code == 200
    stocks = r.json()
    assert len(stocks) == 1
    s = stocks[0]
    assert s['id'] == '2330'
    assert s['name'] == '台積電'
    assert isinstance(s['price'], float)
    assert s['articleCount'] == 42
    assert s['topicInvested'] == pytest.approx(461413362216.5)

def test_get_topic_stocks_not_found(client):
    r = client.get('/api/topics/不存在主題/stocks')
    assert r.status_code == 404

def test_get_topics_invalid_level(client):
    r = client.get('/api/topics?level=invalid')
    assert r.status_code == 400
```

- [ ] **Step 2：確認測試因無端點而失敗**

```bash
python -m pytest tests/test_topics_api.py -v 2>&1 | head -20
```

Expected: `404 Not Found` 或 `422 Unprocessable Entity`（端點不存在）

---

## Task 7：實作後端 API 端點

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1：在 `backend/main.py` 末尾加入三個端點**

在 `get_stock` 函式之後（檔案末尾）新增：

```python
# ── NLP 主題 API ──────────────────────────────────────────────────────────────

def _topic_row(r) -> dict:
    return {
        'id':           r['id'],
        'name':         r['name'],
        'level':        r['level'],
        'parentId':     r['parent_id'],
        'totalInvested': r['total_invested'],
        'articleCount': r['article_count'],
        'stockCount':   r['stock_count'],
    }


@app.get('/api/topics')
def get_topics(level: str = 'medium'):
    if level not in ('medium', 'fine'):
        raise HTTPException(status_code=400, detail='level must be medium or fine')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
            'FROM nlp_topics WHERE level = ? ORDER BY total_invested DESC',
            (level,),
        ).fetchall()
    finally:
        conn.close()
    return [_topic_row(r) for r in rows]


@app.get('/api/topics/{name}/children')
def get_topic_children(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        parent = conn.execute(
            "SELECT id FROM nlp_topics WHERE name = ? AND level = 'medium'", (name,)
        ).fetchone()
        if parent is None:
            raise HTTPException(status_code=404, detail='Topic not found')
        rows = conn.execute(
            'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
            'FROM nlp_topics WHERE parent_id = ? ORDER BY total_invested DESC',
            (parent['id'],),
        ).fetchall()
    finally:
        conn.close()
    return [_topic_row(r) for r in rows]


_TOPIC_SORT: dict[str, str] = {
    'change': 'CAST(REPLACE(REPLACE(s.change_pct,"+",""),"%","") AS REAL)',
    'volume': 's.volume',
    'heat':   'ts.article_count',
}


@app.get('/api/topics/{name}/stocks')
def get_topic_stocks(name: str, level: str = 'medium',
                     sort: str = 'heat', order: str = 'desc'):
    if level not in ('medium', 'fine'):
        raise HTTPException(status_code=400, detail='level must be medium or fine')
    sort_col = _TOPIC_SORT.get(sort, _TOPIC_SORT['heat'])
    dir_ = 'ASC' if order == 'asc' else 'DESC'
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        topic = conn.execute(
            'SELECT id FROM nlp_topics WHERE name = ? AND level = ?', (name, level)
        ).fetchone()
        if topic is None:
            raise HTTPException(status_code=404, detail='Topic not found')
        rows = conn.execute(
            f'''
            SELECT s.stock_code, s.stock_name, s.close_price,
                   s.change_val, s.change_pct, s.volume,
                   ts.article_count, ts.total_invested
            FROM nlp_topic_stocks ts
            JOIN tw_stock_list s ON s.stock_code = ts.stock_code
            WHERE ts.topic_id = ? AND s.close_price IS NOT NULL
            ORDER BY {sort_col} {dir_}
            ''',
            (topic['id'],),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            'id':            r['stock_code'],
            'name':          r['stock_name'],
            'price':         float(r['close_price']),
            'change':        _parse_float(r['change_val']),
            'changePercent': _parse_float(r['change_pct']),
            'volume':        _parse_volume(r['volume']),
            'articleCount':  r['article_count'],
            'topicInvested': r['total_invested'],
        }
        for r in rows
    ]
```

- [ ] **Step 2：執行所有後端測試**

```bash
python -m pytest tests/test_topics_api.py tests/test_backend.py -v
```

Expected: 全部 PASSED

- [ ] **Step 3：Commit**

```bash
git add backend/main.py tests/test_topics_api.py
git commit -m "feat(api): add /api/topics endpoints for NLP topic classification"
```

---

## Task 8：建立 frontend/src/hooks/useTopics.ts

**Files:**
- Create: `frontend/src/hooks/useTopics.ts`

- [ ] **Step 1：建立 hook 檔案**

```typescript
// frontend/src/hooks/useTopics.ts
import { useState, useEffect } from 'react'

export interface Topic {
  id: number
  name: string
  level: 'medium' | 'fine'
  parentId: number | null
  totalInvested: number
  articleCount: number
  stockCount: number
}

export interface TopicStock {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  articleCount: number
  topicInvested: number
}

export function useTopics(level: 'medium' | 'fine' = 'medium'): Topic[] {
  const [topics, setTopics] = useState<Topic[]>([])
  useEffect(() => {
    fetch(`/api/topics?level=${level}`)
      .then((r) => r.json())
      .then(setTopics)
      .catch(() => setTopics([]))
  }, [level])
  return topics
}

export function useTopicChildren(name: string): Topic[] {
  const [children, setChildren] = useState<Topic[]>([])
  useEffect(() => {
    if (!name) { setChildren([]); return }
    fetch(`/api/topics/${encodeURIComponent(name)}/children`)
      .then((r) => r.json())
      .then(setChildren)
      .catch(() => setChildren([]))
  }, [name])
  return children
}

export type TopicSortKey = 'change' | 'volume' | 'heat'

export function useTopicStocks(
  name: string,
  level: 'medium' | 'fine',
  sort: TopicSortKey,
  order: 'asc' | 'desc',
): { stocks: TopicStock[]; loading: boolean } {
  const [stocks, setStocks] = useState<TopicStock[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!name) return
    setLoading(true)
    fetch(
      `/api/topics/${encodeURIComponent(name)}/stocks?level=${level}&sort=${sort}&order=${order}`,
    )
      .then((r) => r.json())
      .then((data) => { setStocks(data); setLoading(false) })
      .catch(() => { setStocks([]); setLoading(false) })
  }, [name, level, sort, order])
  return { stocks, loading }
}
```

- [ ] **Step 2：確認 TypeScript 型別正確**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤輸出

---

## Task 9：建立 frontend/src/components/TopicTab.tsx

**Files:**
- Create: `frontend/src/components/TopicTab.tsx`

- [ ] **Step 1：建立 TopicTab 組件**

```tsx
// frontend/src/components/TopicTab.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { useTopics, useTopicChildren, Topic } from '../hooks/useTopics'

function fmtInvested(n: number): string {
  if (n >= 1e8) return `${(n / 1e8).toFixed(0)}億`
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}萬`
  return n.toFixed(0)
}

function FineRow({ topic, maxInvested }: { topic: Topic; maxInvested: number }) {
  const navigate = useNavigate()
  const barW = maxInvested > 0 ? Math.round((topic.totalInvested / maxInvested) * 100) : 0
  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70"
      onClick={() => navigate(`/topic/fine/${encodeURIComponent(topic.name)}`)}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-[#bbb] text-sm">{topic.name}</span>
        <span className="text-[#999] text-sm">{fmtInvested(topic.totalInvested)}</span>
      </div>
      <div className="h-1 bg-[#2e2e2e] rounded-full overflow-hidden mb-1">
        <div className="h-full bg-[#3a7bd5] rounded-full" style={{ width: `${barW}%` }} />
      </div>
      <span className="text-[#555] text-xs">{topic.stockCount}支 · {topic.articleCount}篇</span>
    </div>
  )
}

function MediumCard({
  topic,
  maxInvested,
  expanded,
  onToggle,
}: {
  topic: Topic
  maxInvested: number
  expanded: boolean
  onToggle: () => void
}) {
  const navigate = useNavigate()
  const children = useTopicChildren(expanded ? topic.name : '')
  const childMax = children.length > 0
    ? Math.max(...children.map((c) => c.totalInvested))
    : 1
  const barW = maxInvested > 0 ? Math.round((topic.totalInvested / maxInvested) * 100) : 0

  return (
    <div className="bg-[#1e1e1e] rounded-[10px] overflow-hidden">
      <div className="px-4 py-3 cursor-pointer active:opacity-70" onClick={onToggle}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-medium">{topic.name}</span>
          <div className="flex items-center gap-2">
            <span className="text-[#aaa] text-sm">{fmtInvested(topic.totalInvested)}</span>
            <button
              className="text-[#2dba6a] active:opacity-60"
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/topic/medium/${encodeURIComponent(topic.name)}`)
              }}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
        <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
          <div className="h-full bg-[#3a7bd5] rounded-full" style={{ width: `${barW}%` }} />
        </div>
        <span className="text-[#555] text-xs">{topic.stockCount}支 · {topic.articleCount}篇</span>
      </div>

      {expanded && children.length > 0 && (
        <div>
          {children.map((child) => (
            <FineRow key={child.id} topic={child} maxInvested={childMax} />
          ))}
        </div>
      )}
    </div>
  )
}

export function TopicTab() {
  const topics = useTopics('medium')
  const [expandedName, setExpandedName] = useState<string | null>(null)
  const maxInvested = topics.length > 0 ? Math.max(...topics.map((t) => t.totalInvested)) : 1

  return (
    <div className="space-y-2">
      {topics.length === 0 && (
        <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
      )}
      {topics.map((topic) => (
        <MediumCard
          key={topic.id}
          topic={topic}
          maxInvested={maxInvested}
          expanded={expandedName === topic.name}
          onToggle={() =>
            setExpandedName((prev) => (prev === topic.name ? null : topic.name))
          }
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 2：TypeScript 型別檢查**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤

---

## Task 10：改造 MarketPage SectorTab — 加類股/主題 toggle

**Files:**
- Modify: `frontend/src/pages/MarketPage.tsx`

- [ ] **Step 1：在頂部 import 加入 TopicTab**

在 `MarketPage.tsx` 頂部找到 import 區塊，加入：

```typescript
import { TopicTab } from '../components/TopicTab'
```

- [ ] **Step 2：在 SectorTab function 頂部加入 view state**

找到 `function SectorTab()` 定義（約在第 193 行附近），在其內部第一個 `const [sortIdx...` 之前加入：

```typescript
  const [view, setView] = useState<'sector' | 'topic'>('sector')
```

- [ ] **Step 3：在 SectorTab return 內容最頂部加入 toggle，並在 view==='topic' 時渲染 TopicTab**

找到 SectorTab 的 `return (` 開頭，將整個 return 替換為：

```tsx
  return (
    <div className="px-3 pt-3 pb-6">
      {/* 類股 / 主題 toggle */}
      <div className="flex gap-2 mb-3">
        {(['sector', 'topic'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={clsx(
              'px-4 py-1.5 text-sm rounded-full font-medium',
              v === view ? 'bg-[#2dba6a] text-white' : 'bg-[#2a2a2a] text-[#888]',
            )}
          >
            {v === 'sector' ? '類股' : '主題'}
          </button>
        ))}
      </div>

      {view === 'topic' ? (
        <TopicTab />
      ) : (
        <>
          {/* Sort tabs */}
          <div className="flex border-b border-[#2e2e2e] mb-3">
            {sectorSortTabs.map((t, i) => (
              <button
                key={t}
                onClick={() => handleSortTab(i)}
                className={clsx(
                  'flex items-center gap-1 mr-5 pb-2.5 text-sm font-medium relative',
                  i === sortIdx ? 'text-[#2dba6a]' : 'text-[#888]',
                )}
              >
                {t}
                {i === sortIdx && <OrderIcon size={12} />}
                {i === sortIdx && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
                )}
              </button>
            ))}
          </div>

          <div className="space-y-2">
            {sectors.map((sector) => {
              const up   = sector.changePercent >= 0
              const barW = Math.round(
                (sort === 'change' ? Math.abs(sector.changePercent) : sector.totalVolume) / maxVal * 100,
              )
              const rightVal = sort === 'change'
                ? `${up ? '+' : ''}${sector.changePercent.toFixed(2)}%`
                : `${(sector.totalVolume / 1e8).toFixed(1)}億`

              return (
                <div
                  key={sector.name}
                  className="bg-[#1e1e1e] rounded-[10px] px-4 py-3 active:opacity-70 cursor-pointer"
                  onClick={() => navigate(`/sector/${encodeURIComponent(sector.name)}`)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white text-sm font-medium">{sector.name}</span>
                    <span className={clsx(
                      'text-base font-bold',
                      sort === 'change' ? (up ? 'text-[#e84040]' : 'text-[#2dba6a]') : 'text-[#aaa]',
                    )}>
                      {rightVal}
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
                    <div
                      className={clsx('h-full rounded-full',
                        sort === 'change' ? (up ? 'bg-[#e84040]' : 'bg-[#2dba6a]') : 'bg-[#3a7bd5]',
                      )}
                      style={{ width: `${barW}%` }}
                    />
                  </div>
                  <div className="flex gap-3 text-xs text-[#666]">
                    <span className="text-[#e84040]">漲 {sector.advance}</span>
                    <span className="text-[#2dba6a]">跌 {sector.decline}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
```

- [ ] **Step 4：TypeScript 型別檢查**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤

- [ ] **Step 5：Commit**

```bash
git add frontend/src/hooks/useTopics.ts frontend/src/components/TopicTab.tsx frontend/src/pages/MarketPage.tsx
git commit -m "feat(frontend): add TopicTab accordion and sector/topic toggle in MarketPage"
```

---

## Task 11：建立 frontend/src/pages/TopicDetailPage.tsx

**Files:**
- Create: `frontend/src/pages/TopicDetailPage.tsx`

- [ ] **Step 1：建立頁面**

```tsx
// frontend/src/pages/TopicDetailPage.tsx
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowDown, ArrowUp } from 'lucide-react'
import { clsx } from 'clsx'
import { useTopicStocks, TopicSortKey } from '../hooks/useTopics'

const SORT_TABS = ['漲跌幅', '成交量', '討論熱度'] as const
const SORT_KEYS: TopicSortKey[] = ['change', 'volume', 'heat']

function fmtInvested(n: number): string {
  if (n >= 1e8) return `${(n / 1e8).toFixed(0)}億`
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}萬`
  return n.toFixed(0)
}

export function TopicDetailPage() {
  const { level, name } = useParams<{ level: string; name: string }>()
  const navigate = useNavigate()
  const [sortIdx, setSortIdx] = useState(0)
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')

  const lv: 'medium' | 'fine' = level === 'fine' ? 'fine' : 'medium'
  const sort = SORT_KEYS[sortIdx]
  const { stocks, loading } = useTopicStocks(name ?? '', lv, sort, order)

  function handleSortTab(i: number) {
    if (i === sortIdx) {
      setOrder((o) => (o === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortIdx(i)
      setOrder('desc')
    }
  }

  const OrderIcon = order === 'desc' ? ArrowDown : ArrowUp

  return (
    <div className="flex flex-col bg-[#111111] min-h-screen">
      {/* Header */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        <div className="flex items-center px-4 pt-14 pb-3 gap-3">
          <button onClick={() => navigate(-1)} className="text-[#888] active:opacity-60">
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-white text-lg font-semibold">{name}</h1>
          <span className="text-[#555] text-xs">{lv === 'medium' ? '中層主題' : '細層主題'}</span>
        </div>

        {/* Sort tabs */}
        <div className="flex border-b border-[#2e2e2e] px-4">
          {SORT_TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => handleSortTab(i)}
              className={clsx(
                'flex items-center gap-1 mr-5 pb-2.5 text-sm font-medium relative',
                i === sortIdx ? 'text-[#2dba6a]' : 'text-[#888]',
              )}
            >
              {t}
              {i === sortIdx && <OrderIcon size={12} />}
              {i === sortIdx && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {loading ? (
          <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
        ) : stocks.length === 0 ? (
          <div className="text-[#666] text-sm text-center pt-10">此主題暫無資料</div>
        ) : (
          <div className="space-y-2">
            {stocks.map((s, idx) => {
              const up = s.changePercent >= 0
              return (
                <div
                  key={s.id}
                  className="bg-[#1e1e1e] rounded-[10px] px-4 py-3 cursor-pointer active:opacity-70"
                  onClick={() => navigate(`/stock/${s.id}`)}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[#555] text-xs w-5">{idx + 1}</span>
                      <div>
                        <span className="text-white text-sm font-medium">{s.name}</span>
                        <span className="text-[#555] text-xs ml-1.5">{s.id}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white text-sm font-medium">{s.price.toFixed(2)}</div>
                      <div className={clsx('text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                        {up ? '+' : ''}{s.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 text-xs text-[#555]">
                    <span>投入 {fmtInvested(s.topicInvested)}</span>
                    <span>·</span>
                    <span>討論 {s.articleCount} 篇</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2：TypeScript 型別檢查**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤

---

## Task 12：新增路由並整合驗收

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1：在 App.tsx 加入 TopicDetailPage import 和路由**

找到 `import { SectorDetailPage }` 那行，在其後加入：

```typescript
import { TopicDetailPage } from './pages/TopicDetailPage'
```

找到 `<Route path="/chain/:name" element={<SectorDetailPage kind="chain" />} />` 那行，在其後加入：

```tsx
<Route path="/topic/:level/:name" element={<TopicDetailPage />} />
```

- [ ] **Step 2：啟動後端**

```bash
cd /Users/wayneho/EventCorr && uvicorn backend.main:app --reload --port 8000
```

- [ ] **Step 3：啟動前端**

新開 terminal：

```bash
cd frontend && npm run dev
```

- [ ] **Step 4：手動驗收清單**

瀏覽器開啟 `http://localhost:5173`，依序確認：

1. 行情 → 類股 tab → 看到 `[類股] [主題]` toggle
2. 點「主題」→ 顯示 medium 主題 accordion 列表（按投入金額排序）
3. 點一個 medium 主題 card → 展開 fine 子主題
4. 點 fine 子主題 → 進入 TopicDetailPage，顯示個股列表
5. 切換排序（漲跌幅 / 成交量 / 討論熱度）→ 列表重排
6. 點個股 → 進入 StockDetailPage（確認不 crash）
7. 點 medium 主題的 `>` 箭頭 → 進入 medium 主題的個股列表

- [ ] **Step 5：Final Commit**

```bash
git add frontend/src/App.tsx frontend/src/pages/TopicDetailPage.tsx
git commit -m "feat(frontend): add TopicDetailPage and /topic/:level/:name route"
```
