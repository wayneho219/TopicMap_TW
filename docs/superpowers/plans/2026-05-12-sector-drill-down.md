# Sector Drill-Down Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將「行情 → 類股」tab 的「類股」view 改為兩層 accordion（major_industry → chain_topic/NLP 主題），並加入 LLM 自動分類腳本把產業相關 NLP fine 主題補充進去。

**Architecture:** tpex_industry_chain DB 提供固定大類與概念股鏈，nlp_topics DB 的 fine 主題透過 Claude Haiku API 分類後存入新表 `nlp_topic_industry_map`，後端新增兩支 API 混合兩個資料來源，前端 IndustryTab 組件仿照現有 TopicTab 實作 accordion。

**Tech Stack:** Python 3.9 + FastAPI + SQLite（後端）、TypeScript + React + Vite（前端）、anthropic SDK（LLM 分類）、pytest + FastAPI TestClient（測試）

---

## File Map

| 動作 | 路徑 |
|---|---|
| 修改 | `requirements.txt` |
| 新增 | `scripts/classify_nlp_topics.py` |
| 修改 | `backend/main.py` |
| 新增 | `tests/test_industries_api.py` |
| 新增 | `tests/test_classify_nlp_topics.py` |
| 修改 | `frontend/src/hooks/useMarketData.ts` |
| 新增 | `frontend/src/components/IndustryTab.tsx` |
| 修改 | `frontend/src/pages/MarketPage.tsx` |

---

## Task 1: DB Migration + 依賴更新

**Files:**
- Modify: `requirements.txt`
- Modify: `data/tw_stock_list.sqlite3`（執行 migration SQL）

- [ ] **Step 1: 在 requirements.txt 加入 anthropic**

開啟 `requirements.txt`，在末尾加入：
```
anthropic>=0.30.0
```

- [ ] **Step 2: 安裝新依賴**

```bash
pip install anthropic
```

Expected: 成功安裝，無錯誤

- [ ] **Step 3: 建立 nlp_topic_industry_map 表**

```bash
python - <<'EOF'
import sqlite3, os
db = os.path.join('data', 'tw_stock_list.sqlite3')
conn = sqlite3.connect(db)
conn.execute('''
    CREATE TABLE IF NOT EXISTS nlp_topic_industry_map (
        topic_id       INTEGER PRIMARY KEY,
        is_industry    INTEGER NOT NULL DEFAULT 0,
        major_industry TEXT,
        classified_at  TEXT NOT NULL
    )
''')
conn.commit()
conn.close()
print("OK: nlp_topic_industry_map created")
EOF
```

Expected output: `OK: nlp_topic_industry_map created`

- [ ] **Step 4: 確認 table 已建立**

```bash
sqlite3 data/tw_stock_list.sqlite3 ".tables"
```

Expected: 輸出中含 `nlp_topic_industry_map`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "feat(deps): add anthropic SDK and create nlp_topic_industry_map table"
```

---

## Task 2: 後端 API 測試（先寫測試）

**Files:**
- Create: `tests/test_industries_api.py`

- [ ] **Step 1: 建立測試檔案**

新增 `tests/test_industries_api.py`：

```python
import os
import sqlite3
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

def _seed_main(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE tw_stock_list (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL DEFAULT '',
            industry_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            source_as_of TEXT NOT NULL DEFAULT '',
            synced_at TEXT NOT NULL DEFAULT '',
            close_price REAL,
            change_val TEXT,
            change_pct TEXT,
            volume INTEGER
        );
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
            PRIMARY KEY (topic_id, stock_code)
        );
        CREATE TABLE nlp_topic_industry_map (
            topic_id       INTEGER PRIMARY KEY,
            is_industry    INTEGER NOT NULL DEFAULT 0,
            major_industry TEXT,
            classified_at  TEXT NOT NULL
        );
        INSERT INTO tw_stock_list(stock_code, stock_name, close_price, change_val, change_pct, volume)
            VALUES
            ('2330','台積電',1000.0,'+35','+3.50%',42000000),
            ('2454','聯發科', 800.0,'+10','+1.25%',10000000),
            ('3481','群創',  15.0,'-0.5','-3.23%', 5000000);
        INSERT INTO nlp_topics VALUES (1,'AI伺服器','fine',NULL,100000,10,2);
        INSERT INTO nlp_topic_stocks VALUES (1,'2330');
        INSERT INTO nlp_topic_stocks VALUES (1,'2454');
        INSERT INTO nlp_topic_industry_map VALUES (1,1,'半導體','2026-01-01T00:00:00');
    ''')
    conn.commit()
    conn.close()

def _seed_chain(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE tpex_industry_chain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_industry TEXT NOT NULL,
            chain_ic TEXT NOT NULL,
            chain_topic TEXT NOT NULL,
            segment_code TEXT NOT NULL,
            segment_name TEXT NOT NULL,
            listing_bucket TEXT NOT NULL DEFAULT '',
            stock_code TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        );
        INSERT INTO tpex_industry_chain(major_industry,chain_ic,chain_topic,segment_code,segment_name,stock_code,stock_name,scraped_at)
            VALUES
            ('半導體','D000','半導體','D001','IC設計','2454','聯發科','2026-01-01'),
            ('半導體','D000','半導體','D001','IC設計','2330','台積電','2026-01-01'),
            ('半導體','D000','晶圓代工','D002','晶圓廠','3481','群創','2026-01-01');
    ''')
    conn.commit()
    conn.close()

@pytest.fixture
def client(tmp_path):
    main_db   = str(tmp_path / 'main.sqlite3')
    chain_db  = str(tmp_path / 'chain.sqlite3')
    _seed_main(main_db)
    _seed_chain(chain_db)

    import backend.main as m
    orig_db       = m.DB_PATH
    orig_chain_db = m.DB_CHAIN_PATH
    m.DB_PATH       = main_db
    m.DB_CHAIN_PATH = chain_db
    yield TestClient(m.app)
    m.DB_PATH       = orig_db
    m.DB_CHAIN_PATH = orig_chain_db

# ── /api/market/industries ──────────────────────────────────────

def test_get_industries_returns_list(client):
    r = client.get('/api/market/industries')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    item = data[0]
    assert item['name'] == '半導體'
    assert 'topicCount' in item
    assert 'advance' in item
    assert 'decline' in item
    assert 'changePercent' in item

def test_get_industries_topic_count_includes_nlp(client):
    r = client.get('/api/market/industries')
    data = r.json()
    # chain_topics: 半導體, 晶圓代工 = 2, NLP: AI伺服器 = 1 → total 3
    assert data[0]['topicCount'] == 3

def test_get_industries_advance_decline(client):
    r = client.get('/api/market/industries')
    data = r.json()
    # 2330 +3.50%, 2454 +1.25% → advance=2; 3481 -3.23% → decline=1
    assert data[0]['advance'] == 2
    assert data[0]['decline'] == 1

def test_get_industries_sort_order(client):
    r = client.get('/api/market/industries?sort=change&order=desc')
    assert r.status_code == 200

# ── /api/market/industry/{name}/topics ──────────────────────────

def test_get_industry_topics_contains_tpex(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    assert r.status_code == 200
    data = r.json()
    names = [t['name'] for t in data]
    assert '半導體' in names
    assert '晶圓代工' in names

def test_get_industry_topics_contains_nlp(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    data = r.json()
    nlp_items = [t for t in data if t['source'] == 'nlp']
    assert len(nlp_items) == 1
    assert nlp_items[0]['name'] == 'AI伺服器'

def test_get_industry_topics_source_field(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    data = r.json()
    for t in data:
        assert t['source'] in ('tpex', 'nlp')
        assert 'changePercent' in t
        assert 'stockCount' in t

def test_get_industry_topics_unknown_returns_empty(client):
    r = client.get('/api/market/industry/%E4%B8%8D%E5%AD%98%E5%9C%A8/topics')
    assert r.status_code == 200
    assert r.json() == []
```

- [ ] **Step 2: 確認測試失敗（API 尚未實作）**

```bash
cd /Users/wayneho/EventCorr && python -m pytest tests/test_industries_api.py -v 2>&1 | tail -20
```

Expected: 多個 FAILED（404 或 AttributeError）

- [ ] **Step 3: Commit 測試**

```bash
git add tests/test_industries_api.py
git commit -m "test(api): add failing tests for /api/market/industries and /api/market/industry/{name}/topics"
```

---

## Task 3: 後端 API 實作

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 在 main.py 頂部加入 collections 引用**

在 `backend/main.py` 的 import 區塊末尾加入：

```python
from collections import defaultdict
```

- [ ] **Step 2: 在 main.py 末尾加入兩支 endpoint**

在 `backend/main.py` 的最末加入：

```python
@app.get('/api/market/industries')
def get_industries(sort: str = 'change', order: str = 'desc'):
    chain_conn = sqlite3.connect(DB_CHAIN_PATH)
    chain_conn.row_factory = sqlite3.Row
    try:
        all_chain = chain_conn.execute(
            'SELECT major_industry, stock_code FROM tpex_industry_chain'
        ).fetchall()
        topic_count_rows = chain_conn.execute(
            'SELECT major_industry, COUNT(DISTINCT chain_topic) AS cnt '
            'FROM tpex_industry_chain GROUP BY major_industry'
        ).fetchall()
    finally:
        chain_conn.close()

    chain_topic_counts: dict[str, int] = {r['major_industry']: r['cnt'] for r in topic_count_rows}

    industry_stocks: dict[str, set] = defaultdict(set)
    for r in all_chain:
        industry_stocks[r['major_industry']].add(r['stock_code'])

    all_codes = list({c for codes in industry_stocks.values() for c in codes})
    if not all_codes:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        nlp_counts_rows = conn.execute(
            '''SELECT m.major_industry, COUNT(*) AS cnt
               FROM nlp_topic_industry_map m
               JOIN nlp_topics t ON t.id = m.topic_id
               WHERE m.is_industry = 1 AND t.level = 'fine'
               GROUP BY m.major_industry'''
        ).fetchall()
        nlp_topic_counts: dict[str, int] = {r['major_industry']: r['cnt'] for r in nlp_counts_rows}

        ph = ','.join('?' * len(all_codes))
        price_rows = conn.execute(
            f'''SELECT stock_code,
                       CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) AS chg
                FROM tw_stock_list
                WHERE stock_code IN ({ph})
                  AND change_pct IS NOT NULL AND change_pct != ""''',
            all_codes,
        ).fetchall()
    finally:
        conn.close()

    price_map: dict[str, float] = {r['stock_code']: r['chg'] for r in price_rows}

    results = []
    for industry, codes in industry_stocks.items():
        changes = [price_map[c] for c in codes if c in price_map]
        if not changes:
            continue
        avg_chg = sum(changes) / len(changes)
        results.append({
            'name':          industry,
            'topicCount':    chain_topic_counts.get(industry, 0) + nlp_topic_counts.get(industry, 0),
            'advance':       sum(1 for c in changes if c > 0),
            'decline':       sum(1 for c in changes if c < 0),
            'changePercent': round(avg_chg, 2),
        })

    sort_key = 'changePercent' if sort == 'change' else 'topicCount'
    results.sort(key=lambda x: x[sort_key], reverse=(order != 'asc'))
    return results


@app.get('/api/market/industry/{name}/topics')
def get_industry_topics(name: str):
    chain_conn = sqlite3.connect(DB_CHAIN_PATH)
    chain_conn.row_factory = sqlite3.Row
    try:
        chain_rows = chain_conn.execute(
            'SELECT chain_topic, stock_code FROM tpex_industry_chain WHERE major_industry = ?',
            (name,),
        ).fetchall()
    finally:
        chain_conn.close()

    topic_stocks: dict[str, set] = defaultdict(set)
    for r in chain_rows:
        topic_stocks[r['chain_topic']].add(r['stock_code'])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        nlp_rows = conn.execute(
            '''SELECT t.id, t.name, t.stock_count
               FROM nlp_topics t
               JOIN nlp_topic_industry_map m ON t.id = m.topic_id
               WHERE m.is_industry = 1 AND m.major_industry = ? AND t.level = 'fine' ''',
            (name,),
        ).fetchall()

        nlp_topic_ids   = [r['id'] for r in nlp_rows]
        nlp_names       = {r['id']: r['name']        for r in nlp_rows}
        nlp_stock_count = {r['id']: r['stock_count'] for r in nlp_rows}

        nlp_stock_map: dict[int, set] = defaultdict(set)
        if nlp_topic_ids:
            ph = ','.join('?' * len(nlp_topic_ids))
            for row in conn.execute(
                f'SELECT topic_id, stock_code FROM nlp_topic_stocks WHERE topic_id IN ({ph})',
                nlp_topic_ids,
            ).fetchall():
                nlp_stock_map[row['topic_id']].add(row['stock_code'])

        all_codes = list(
            {c for codes in topic_stocks.values() for c in codes}
            | {c for codes in nlp_stock_map.values() for c in codes}
        )
        price_map: dict[str, float] = {}
        if all_codes:
            ph = ','.join('?' * len(all_codes))
            for row in conn.execute(
                f'''SELECT stock_code,
                           CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) AS chg
                    FROM tw_stock_list
                    WHERE stock_code IN ({ph})
                      AND change_pct IS NOT NULL AND change_pct != ""''',
                all_codes,
            ).fetchall():
                price_map[row['stock_code']] = row['chg']
    finally:
        conn.close()

    results = []

    for chain_topic, codes in topic_stocks.items():
        changes = [price_map[c] for c in codes if c in price_map]
        avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
        results.append({
            'name':          chain_topic,
            'source':        'tpex',
            'changePercent': avg_chg,
            'stockCount':    len(codes),
        })

    for tid, tname in nlp_names.items():
        codes = nlp_stock_map.get(tid, set())
        changes = [price_map[c] for c in codes if c in price_map]
        avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
        results.append({
            'name':          tname,
            'source':        'nlp',
            'changePercent': avg_chg,
            'stockCount':    nlp_stock_count.get(tid, len(codes)),
        })

    results.sort(key=lambda x: abs(x['changePercent']), reverse=True)
    return results
```

- [ ] **Step 3: 執行測試確認通過**

```bash
cd /Users/wayneho/EventCorr && python -m pytest tests/test_industries_api.py -v
```

Expected: 所有測試 PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat(api): add /api/market/industries and /api/market/industry/{name}/topics endpoints"
```

---

## Task 4: LLM 分類腳本

**Files:**
- Create: `scripts/classify_nlp_topics.py`
- Create: `tests/test_classify_nlp_topics.py`

- [ ] **Step 1: 建立測試檔（mock Claude API）**

新增 `tests/test_classify_nlp_topics.py`：

```python
import sqlite3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from unittest.mock import patch, MagicMock


def _make_response(text: str):
    resp = MagicMock()
    resp.content = [MagicMock(text=text)]
    return resp


def test_classify_topic_industry():
    import scripts.classify_nlp_topics as c
    with patch.object(c.client.messages, 'create',
                      return_value=_make_response('{"is_industry": true, "major_industry": "半導體"}')):
        result = c.classify_topic('台積電股')
    assert result['is_industry'] is True
    assert result['major_industry'] == '半導體'


def test_classify_topic_noise():
    import scripts.classify_nlp_topics as c
    with patch.object(c.client.messages, 'create',
                      return_value=_make_response('{"is_industry": false, "major_industry": null}')):
        result = c.classify_topic('個股閒聊')
    assert result['is_industry'] is False
    assert result['major_industry'] is None


def test_run_incremental(tmp_path):
    db = str(tmp_path / 'test.sqlite3')
    conn = sqlite3.connect(db)
    conn.executescript('''
        CREATE TABLE nlp_topics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            level TEXT NOT NULL
        );
        CREATE TABLE nlp_topic_industry_map (
            topic_id       INTEGER PRIMARY KEY,
            is_industry    INTEGER NOT NULL DEFAULT 0,
            major_industry TEXT,
            classified_at  TEXT NOT NULL
        );
        INSERT INTO nlp_topics VALUES (1,'台積電股','fine');
        INSERT INTO nlp_topics VALUES (2,'個股閒聊','fine');
        INSERT INTO nlp_topics VALUES (3,'medium主題','medium');
        -- topic_id=2 already classified; should be skipped
        INSERT INTO nlp_topic_industry_map VALUES (2,0,NULL,'2026-01-01');
    ''')
    conn.commit()
    conn.close()

    import scripts.classify_nlp_topics as c
    original_db = c.DB_PATH
    c.DB_PATH = db
    try:
        with patch.object(c.client.messages, 'create',
                          return_value=_make_response('{"is_industry": true, "major_industry": "半導體"}')):
            c.run()
    finally:
        c.DB_PATH = original_db

    conn2 = sqlite3.connect(db)
    rows = conn2.execute('SELECT topic_id, is_industry, major_industry FROM nlp_topic_industry_map ORDER BY topic_id').fetchall()
    conn2.close()
    # Only topic_id=1 (fine, unclassified) should be newly inserted; topic_id=2 unchanged; topic_id=3 (medium) skipped
    assert len(rows) == 2
    assert rows[0] == (1, 1, '半導體')
    assert rows[1] == (2, 0, None)
```

- [ ] **Step 2: 確認測試失敗（腳本尚未存在）**

```bash
cd /Users/wayneho/EventCorr && python -m pytest tests/test_classify_nlp_topics.py -v 2>&1 | tail -10
```

Expected: `ModuleNotFoundError: No module named 'scripts.classify_nlp_topics'`

- [ ] **Step 3: 建立分類腳本**

新增 `scripts/classify_nlp_topics.py`：

```python
import anthropic
import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

client = anthropic.Anthropic()

MAJOR_INDUSTRIES = [
    "交通運輸及航運", "休閒娛樂", "其他", "前瞻科技", "半導體", "印刷電路板",
    "平面顯示器", "建材營造", "數位科技", "文化創意", "水泥", "汽車",
    "油電燃氣", "生技醫療", "石化及塑橡膠", "紡織", "綠色能源", "自動化",
    "被動元件", "觸控面板", "貿易百貨", "軟體服務", "通信網路", "造紙",
    "連接器", "金融", "鋼鐵", "電子商務", "電機機械", "電腦週邊", "食品",
]

_SYSTEM = (
    "你是台灣股市產業分類專家。判斷 NLP 聚類主題是否為「產業/行業主題」（非閒聊、情緒、政治）。\n"
    f"可選大類（只能選一個，或 null）：{json.dumps(MAJOR_INDUSTRIES, ensure_ascii=False)}"
)


def classify_topic(name: str) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f'主題名稱：「{name}」\n'
                '僅回覆 JSON：{"is_industry": true/false, "major_industry": "xxx" or null}'
            ),
        }],
    )
    return json.loads(resp.content[0].text)


def run() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    topics = conn.execute(
        '''SELECT t.id, t.name FROM nlp_topics t
           LEFT JOIN nlp_topic_industry_map m ON t.id = m.topic_id
           WHERE t.level = 'fine' AND m.topic_id IS NULL'''
    ).fetchall()

    now = datetime.now(timezone.utc).isoformat()
    for topic in topics:
        result = classify_topic(topic['name'])
        conn.execute(
            'INSERT OR REPLACE INTO nlp_topic_industry_map '
            '(topic_id, is_industry, major_industry, classified_at) VALUES (?, ?, ?, ?)',
            (
                topic['id'],
                1 if result.get('is_industry') else 0,
                result.get('major_industry'),
                now,
            ),
        )
        conn.commit()
        label = '產業' if result.get('is_industry') else '雜訊'
        mapped = result.get('major_industry') or ''
        print(f"  {topic['name']} → {label} {mapped}")

    conn.close()


if __name__ == '__main__':
    run()
```

- [ ] **Step 4: 執行測試確認通過**

```bash
cd /Users/wayneho/EventCorr && python -m pytest tests/test_classify_nlp_topics.py -v
```

Expected: 所有測試 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/classify_nlp_topics.py tests/test_classify_nlp_topics.py
git commit -m "feat(script): add classify_nlp_topics.py to classify NLP fine topics via Claude API"
```

---

## Task 5: 前端 Hooks

**Files:**
- Modify: `frontend/src/hooks/useMarketData.ts`

- [ ] **Step 1: 在 useMarketData.ts 末尾加入兩個 interface 和兩個 hook**

開啟 `frontend/src/hooks/useMarketData.ts`，在檔案末尾加入：

```typescript
export interface IndustryData {
  name: string
  topicCount: number
  advance: number
  decline: number
  changePercent: number
}

export interface IndustryTopic {
  name: string
  source: 'tpex' | 'nlp'
  changePercent: number
  stockCount: number
}

export function useIndustries(
  sort: 'change' | 'volume' = 'change',
  order: 'asc' | 'desc' = 'desc',
): IndustryData[] {
  const [industries, setIndustries] = useState<IndustryData[]>([])
  useEffect(() => {
    fetch(`/api/market/industries?sort=${sort}&order=${order}`)
      .then((r) => r.json())
      .then((data: IndustryData[]) => setIndustries(data))
      .catch(() => {})
  }, [sort, order])
  return industries
}

export function useIndustryTopics(name: string): IndustryTopic[] {
  const [topics, setTopics] = useState<IndustryTopic[]>([])
  useEffect(() => {
    if (!name) { setTopics([]); return }
    fetch(`/api/market/industry/${encodeURIComponent(name)}/topics`)
      .then((r) => r.json())
      .then((data: IndustryTopic[]) => setTopics(data))
      .catch(() => {})
  }, [name])
  return topics
}
```

- [ ] **Step 2: 確認 TypeScript 無型別錯誤**

```bash
cd /Users/wayneho/EventCorr/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤輸出

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useMarketData.ts
git commit -m "feat(hooks): add useIndustries and useIndustryTopics to useMarketData"
```

---

## Task 6: 前端 UI — IndustryTab 組件

**Files:**
- Create: `frontend/src/components/IndustryTab.tsx`

- [ ] **Step 1: 建立 IndustryTab.tsx**

新增 `frontend/src/components/IndustryTab.tsx`：

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { useIndustries, useIndustryTopics } from '../hooks/useMarketData'
import type { IndustryData, IndustryTopic } from '../hooks/useMarketData'

function TopicRow({ topic }: { topic: IndustryTopic }) {
  const navigate = useNavigate()
  const up = topic.changePercent >= 0

  function handleClick() {
    if (topic.source === 'tpex') {
      navigate(`/chain/${encodeURIComponent(topic.name)}`)
    } else {
      navigate(`/topic/fine/${encodeURIComponent(topic.name)}`)
    }
  }

  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70 flex items-center justify-between"
      onClick={handleClick}
    >
      <div className="flex items-center gap-2">
        <span className="text-[#bbb] text-sm">{topic.name}</span>
        {topic.source === 'nlp' && (
          <span className="text-[10px] text-[#3a7bd5] bg-[#1a2a40] px-1 py-0.5 rounded leading-none">
            ✦
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#666]">{topic.stockCount}支</span>
        <span className={clsx('text-sm font-medium', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {up ? '+' : ''}{topic.changePercent.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}

function IndustryCard({
  industry,
  maxChange,
  expanded,
  onToggle,
}: {
  industry: IndustryData
  maxChange: number
  expanded: boolean
  onToggle: () => void
}) {
  const topics = useIndustryTopics(expanded ? industry.name : '')
  const up = industry.changePercent >= 0
  const barW = maxChange > 0
    ? Math.round((Math.abs(industry.changePercent) / maxChange) * 100)
    : 0

  return (
    <div className="bg-[#1e1e1e] rounded-[10px] overflow-hidden">
      <div className="px-4 py-3 cursor-pointer active:opacity-70" onClick={onToggle}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-medium">{industry.name}</span>
          <div className="flex items-center gap-2">
            <span className={clsx('text-base font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
              {up ? '+' : ''}{industry.changePercent.toFixed(2)}%
            </span>
            <ChevronRight
              size={16}
              className={clsx(
                'text-[#2dba6a] transition-transform duration-200',
                expanded && 'rotate-90',
              )}
            />
          </div>
        </div>
        <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
          <div
            className={clsx('h-full rounded-full', up ? 'bg-[#e84040]' : 'bg-[#2dba6a]')}
            style={{ width: `${barW}%` }}
          />
        </div>
        <div className="flex gap-3 text-xs text-[#666]">
          <span>{industry.topicCount}個主題</span>
          <span className="text-[#e84040]">漲 {industry.advance}</span>
          <span className="text-[#2dba6a]">跌 {industry.decline}</span>
        </div>
      </div>

      {expanded && topics.length > 0 && (
        <div>
          {topics.map((t) => (
            <TopicRow key={`${t.source}-${t.name}`} topic={t} />
          ))}
        </div>
      )}
      {expanded && topics.length === 0 && (
        <div className="pl-6 py-3 text-[#555] text-xs border-t border-[#252525]">載入中...</div>
      )}
    </div>
  )
}

export function IndustryTab() {
  const industries = useIndustries()
  const [expandedName, setExpandedName] = useState<string | null>(null)
  const maxChange = industries.length > 0
    ? Math.max(...industries.map((i) => Math.abs(i.changePercent)))
    : 1

  if (industries.length === 0) {
    return <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
  }

  return (
    <div className="space-y-2">
      {industries.map((industry) => (
        <IndustryCard
          key={industry.name}
          industry={industry}
          maxChange={maxChange}
          expanded={expandedName === industry.name}
          onToggle={() =>
            setExpandedName((prev) => (prev === industry.name ? null : industry.name))
          }
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: 確認 TypeScript 無型別錯誤**

```bash
cd /Users/wayneho/EventCorr/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/IndustryTab.tsx
git commit -m "feat(ui): add IndustryTab component with two-level accordion"
```

---

## Task 7: 接入 MarketPage

**Files:**
- Modify: `frontend/src/pages/MarketPage.tsx`

- [ ] **Step 1: 修改 MarketPage.tsx**

在 `frontend/src/pages/MarketPage.tsx`：

**①** 修改 lucide-react import，移除已不再使用的 `ArrowUp`、`ArrowDown`：

```typescript
import { Search } from 'lucide-react'
```

**②** 修改 useMarketData import，移除 `useSectors`：

```typescript
import { useMarketHot, useSearchHot } from '../hooks/useMarketData'
```

**③** 加入 IndustryTab import：

```typescript
import { IndustryTab } from '../components/IndustryTab'
```

**④** 刪除檔案頂層的三個宣告（`SectorTab` 函式體外）：
```typescript
// 刪除以下三行：
const sectorSortTabs = ['漲跌幅', '成交量'] as const
type SectorSort = 'change' | 'volume'
type SectorOrder = 'asc' | 'desc'
```

**⑤** 將整個 `SectorTab` 函式改為：

```tsx
function SectorTab() {
  const [view, setView] = useState<'sector' | 'topic'>('sector')

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

      {view === 'topic' ? <TopicTab /> : <IndustryTab />}
    </div>
  )
}
```

（上述修改已涵蓋所有清理項目）

- [ ] **Step 2: 確認 TypeScript 無型別錯誤**

```bash
cd /Users/wayneho/EventCorr/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: 無錯誤

- [ ] **Step 3: 啟動開發伺服器確認 UI**

先啟動後端：
```bash
cd /Users/wayneho/EventCorr && uvicorn backend.main:app --reload --port 8000 &
```

再啟動前端：
```bash
cd /Users/wayneho/EventCorr/frontend && npm run dev
```

打開 http://localhost:5173，操作路徑：
- 行情 → 類股 tab → 確認左側顯示「類股」/「主題」toggle
- 點「類股」→ 確認出現 major_industry 卡片列表（**注意：先執行 classify_nlp_topics.py 後才有 NLP 補充**）
- 點擊任一卡片 → 確認展開顯示 chain_topic 子項目
- 點擊子項目 → 確認跳轉到正確頁面
- 點「主題」→ 確認原有主題 accordion 仍正常運作

- [ ] **Step 4: 執行 NLP 分類腳本（需要 ANTHROPIC_API_KEY）**

```bash
export ANTHROPIC_API_KEY=<your_key>
cd /Users/wayneho/EventCorr && python scripts/classify_nlp_topics.py
```

Expected: 逐行輸出分類結果，如 `台積電股 → 產業 半導體`

- [ ] **Step 5: 確認 NLP 補充主題出現在 UI**

重整頁面，展開某個 major_industry，確認有帶 `✦` 標記的 NLP 主題出現在子項目中。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/MarketPage.tsx
git commit -m "feat(ui): replace SectorTab sector view with IndustryTab accordion"
```
