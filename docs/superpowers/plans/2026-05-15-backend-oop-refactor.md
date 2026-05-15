# Backend OOP Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `backend/main.py` (835 lines, 0 classes) into a 3-layer Router / Service / Repository architecture with Pydantic response schemas, preserving all API paths and response shapes.

**Architecture:** Repositories handle raw SQLite queries and return `sqlite3.Row` objects. Services contain business logic and return typed Pydantic models. Routers are thin — they receive query params, call services, and declare `response_model`. Existing tests must pass throughout.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, sqlite3 (stdlib)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `backend/database.py` | `DB_PATH`, `DB_CHAIN_PATH`, `get_connection()` context manager |
| Create | `backend/schemas.py` | All Pydantic response models |
| Create | `backend/repositories/__init__.py` | empty |
| Create | `backend/repositories/stock.py` | `StockRepository` |
| Create | `backend/repositories/market.py` | `MarketRepository` |
| Create | `backend/repositories/topic.py` | `TopicRepository` |
| Create | `backend/repositories/industry.py` | `IndustryRepository` |
| Create | `backend/services/__init__.py` | empty |
| Create | `backend/services/stock.py` | `StockService` |
| Create | `backend/services/market.py` | `MarketService` |
| Create | `backend/services/topic.py` | `TopicService` |
| Create | `backend/services/industry.py` | `IndustryService` |
| Create | `backend/routers/__init__.py` | empty |
| Create | `backend/routers/stocks.py` | `/api/stocks/*` routes |
| Create | `backend/routers/market.py` | `/api/market/*` routes (hot, sectors, chain, recurring, search_hot) |
| Create | `backend/routers/topics.py` | `/api/topics/*` routes |
| Create | `backend/routers/industries.py` | `/api/market/industries` + `/api/market/industry/*` routes |
| Modify | `backend/main.py` | Thin: app creation, middleware, router registration only |

---

## Task 1: Baseline — run existing tests

**Files:** (none modified)

- [ ] **Step 1: Run all backend tests and record the baseline**

```bash
cd /path/to/EventCorr
python -m pytest tests/test_backend.py tests/test_industries_api.py tests/test_topics_api.py -v 2>&1 | tail -20
```

Expected: some tests may already skip/fail due to missing DB. Record which pass. These must still pass after every subsequent task.

- [ ] **Step 2: Note the passing test names**

Write them down — you'll re-run after each task.

---

## Task 2: Foundation — `database.py` and `schemas.py`

**Files:**
- Create: `backend/database.py`
- Create: `backend/schemas.py`

- [ ] **Step 1: Create `backend/database.py`**

```python
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')
DB_CHAIN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tpex_industry_chain.sqlite3')


@contextmanager
def get_connection(path: str) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

- [ ] **Step 2: Create `backend/schemas.py`**

```python
from pydantic import BaseModel
from typing import Optional


class StockSummary(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int


class RankedStock(BaseModel):
    rank: int
    id: str
    name: str
    price: float
    changePercent: float


class StockSearchResult(BaseModel):
    id: str
    name: str
    market: str
    industry: Optional[str]
    price: float
    change: float
    changePercent: float


class StockDetail(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    market: str
    industry: Optional[str]
    tags: list[str]
    status: str
    high: Optional[float]
    low: Optional[float]
    prevClose: Optional[float]
    open: Optional[float]


class IntradayPoint(BaseModel):
    time: str
    price: float
    volume: int
    pct: float


class SectorSummary(BaseModel):
    name: str
    changePercent: float
    advance: int
    decline: int
    totalVolume: int


class IndustrySummary(BaseModel):
    name: str
    topicCount: int
    advance: int
    decline: int
    changePercent: float
    totalVolume: int
    totalInvested: float


class IndustryTopic(BaseModel):
    name: str
    source: str
    changePercent: float
    stockCount: int


class TopicSummary(BaseModel):
    id: int
    name: str
    level: str
    parentId: Optional[int]
    totalInvested: Optional[float]
    articleCount: Optional[int]
    stockCount: Optional[int]


class TopicStock(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    articleCount: Optional[int]
    topicInvested: Optional[float]
```

- [ ] **Step 3: Verify imports work**

```bash
cd /path/to/EventCorr
python -c "from backend.database import get_connection, DB_PATH; from backend.schemas import StockDetail; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/database.py backend/schemas.py
git commit -m "feat(backend): add database context manager and Pydantic schemas"
```

---

## Task 3: Stock Repository + Service + Router

**Files:**
- Create: `backend/repositories/__init__.py`
- Create: `backend/repositories/stock.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/stock.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/stocks.py`

- [ ] **Step 1: Write failing test for `StockRepository`**

Add to `tests/test_backend.py` (or create `tests/test_stock_repo.py`):

```python
# tests/test_stock_repo.py
import pytest
from unittest.mock import patch, MagicMock
import sqlite3
from backend.repositories.stock import StockRepository


def _make_row(data: dict):
    conn = sqlite3.connect(':memory:')
    conn.execute(
        'CREATE TABLE tw_stock_list (stock_code, stock_name, close_price, '
        'change_val, change_pct, volume, market, industry_name, '
        'high_price, low_price, open_price)'
    )
    conn.execute('INSERT INTO tw_stock_list VALUES (?,?,?,?,?,?,?,?,?,?,?)', [
        data.get('stock_code', '2330'),
        data.get('stock_name', '台積電'),
        data.get('close_price', '1000'),
        data.get('change_val', '10'),
        data.get('change_pct', '+1.01%'),
        data.get('volume', '50000'),
        data.get('market', 'TWSE_LISTED'),
        data.get('industry_name', '半導體業'),
        data.get('high_price', '1010'),
        data.get('low_price', '990'),
        data.get('open_price', '995'),
    ])
    conn.row_factory = sqlite3.Row
    return conn.execute('SELECT * FROM tw_stock_list').fetchone()


def test_stock_repo_find_by_id_returns_none_for_missing():
    repo = StockRepository(':memory:')
    result = repo.find_by_id('XXXX')
    assert result is None


def test_stock_repo_search_returns_empty_for_blank():
    repo = StockRepository(':memory:')
    result = repo.search('')
    assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_stock_repo.py -v
```

Expected: `ImportError` — `StockRepository` not yet defined.

- [ ] **Step 3: Create `backend/repositories/__init__.py`**

```python
```
(empty file)

- [ ] **Step 4: Create `backend/repositories/stock.py`**

```python
import sqlite3
import urllib.request
import json
import datetime
from backend.database import get_connection, DB_PATH

YAHOO_SUFFIX = {
    'TWSE_LISTED': '.TW',
    'TPEX_OTC':    '.TWO',
    'TPEX_EMERGING': '.TWO',
}

TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))


class StockRepository:
    def __init__(self, db_path: str = DB_PATH):
        self._db = db_path

    def find_by_id(self, stock_id: str) -> sqlite3.Row | None:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT * FROM tw_stock_list WHERE stock_code = ?', (stock_id,)
            ).fetchone()

    def get_prices(self, codes: list[str]) -> list[sqlite3.Row]:
        if not codes:
            return []
        ph = ','.join('?' * len(codes))
        with get_connection(self._db) as conn:
            return conn.execute(
                f'SELECT stock_code, stock_name, close_price, change_val, change_pct, volume '
                f'FROM tw_stock_list WHERE stock_code IN ({ph})',
                codes,
            ).fetchall()

    def search(self, q: str, limit: int = 30) -> list[sqlite3.Row]:
        q = q.strip()
        if not q:
            return []
        with get_connection(self._db) as conn:
            return conn.execute(
                '''
                SELECT stock_code, stock_name, market, industry_name,
                       close_price, change_val, change_pct
                FROM tw_stock_list
                WHERE stock_code LIKE ? OR stock_name LIKE ?
                ORDER BY
                    CASE WHEN stock_code = ?   THEN 0
                         WHEN stock_code LIKE ? THEN 1
                         WHEN stock_name LIKE ? THEN 2
                         ELSE 3 END,
                    stock_code
                LIMIT ?
                ''',
                (f'%{q}%', f'%{q}%', q, f'{q}%', f'{q}%', limit),
            ).fetchall()

    def get_topics(self, stock_id: str) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                '''SELECT DISTINCT t.id, t.name, t.level, t.parent_id,
                          t.total_invested, t.article_count, t.stock_count
                   FROM nlp_topics t
                   JOIN nlp_topic_stocks ts ON t.id = ts.topic_id
                   WHERE ts.stock_code = ? AND t.level = 'fine'
                   ORDER BY ts.total_invested DESC''',
                (stock_id,),
            ).fetchall()

    def get_intraday_meta(self, stock_id: str) -> sqlite3.Row | None:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT market, close_price, change_val FROM tw_stock_list WHERE stock_code = ?',
                (stock_id,),
            ).fetchone()

    def fetch_yahoo_intraday(self, stock_id: str, market: str) -> list[dict]:
        suffix = YAHOO_SUFFIX.get(market, '.TW')
        symbol = f'{stock_id}{suffix}'
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())

        result = payload.get('chart', {}).get('result')
        if not result:
            return []

        chart = result[0]
        prev_close = (chart['meta'].get('chartPreviousClose')
                      or chart['meta'].get('previousClose') or 1.0)
        timestamps = chart.get('timestamp', [])
        quotes = chart.get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])
        volumes = quotes.get('volume', [])

        out = []
        for ts, price, vol in zip(timestamps, closes, volumes):
            if price is None:
                continue
            t = datetime.datetime.fromtimestamp(ts, tz=TZ_TAIPEI)
            if t.hour < 9 or (t.hour == 13 and t.minute > 30) or t.hour > 13:
                continue
            pct = (price - prev_close) / prev_close * 100
            out.append({
                'time': t.strftime('%H:%M'),
                'price': round(price, 2),
                'volume': vol or 0,
                'pct': round(pct, 2),
            })
        return out
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_stock_repo.py -v
```

Expected: PASS

- [ ] **Step 6: Create `backend/services/__init__.py`**

```python
```
(empty file)

- [ ] **Step 7: Create `backend/services/stock.py`**

```python
from fastapi import HTTPException
from backend.repositories.stock import StockRepository
from backend.schemas import (
    StockSummary, StockSearchResult, StockDetail,
    TopicSummary, IntradayPoint
)

MARKET_LABEL = {
    'TWSE_LISTED':   '上市',
    'TPEX_OTC':      '上櫃',
    'TPEX_EMERGING': '興櫃',
}


def _parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace('+', '').replace('%', ''))
    except ValueError:
        return 0.0


def _parse_volume(val) -> int:
    if val is None:
        return 0
    try:
        return int(float(str(val)))
    except ValueError:
        return 0


def _tags(market: str) -> list[str]:
    label = MARKET_LABEL.get(market, market)
    return [label, '可現沖'] if market == 'TWSE_LISTED' else [label]


class StockService:
    def __init__(self, repo: StockRepository | None = None):
        self._repo = repo or StockRepository()

    def get_prices(self, codes: list[str]) -> list[StockSummary]:
        rows = self._repo.get_prices(codes)
        order_map = {c: i for i, c in enumerate(codes)}
        result = [
            StockSummary(
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']) if r['close_price'] else 0.0,
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
                volume=_parse_volume(r['volume']),
            )
            for r in rows
        ]
        result.sort(key=lambda x: order_map.get(x.id, 999))
        return result

    def search(self, q: str) -> list[StockSearchResult]:
        rows = self._repo.search(q)
        return [
            StockSearchResult(
                id=r['stock_code'],
                name=r['stock_name'],
                market=r['market'],
                industry=r['industry_name'],
                price=float(r['close_price']) if r['close_price'] is not None else 0.0,
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
            )
            for r in rows
        ]

    def get_stock(self, stock_id: str) -> StockDetail:
        row = self._repo.find_by_id(stock_id)
        if row is None:
            raise HTTPException(status_code=404, detail='Stock not found')
        close = float(row['close_price']) if row['close_price'] is not None else 0.0
        change = _parse_float(row['change_val'])
        prev_close = round(close - change, 2) if close and change else None

        def _opt(val):
            return float(val) if val is not None else None

        return StockDetail(
            id=row['stock_code'],
            name=row['stock_name'],
            price=close,
            change=change,
            changePercent=_parse_float(row['change_pct']),
            volume=_parse_volume(row['volume']),
            market=row['market'],
            industry=row['industry_name'],
            tags=_tags(row['market']),
            status='已收盤',
            high=_opt(row['high_price']),
            low=_opt(row['low_price']),
            prevClose=prev_close,
            open=_opt(row['open_price']),
        )

    def get_topics(self, stock_id: str) -> list[TopicSummary]:
        rows = self._repo.get_topics(stock_id)
        return [
            TopicSummary(
                id=r['id'],
                name=r['name'],
                level=r['level'],
                parentId=r['parent_id'],
                totalInvested=r['total_invested'],
                articleCount=r['article_count'],
                stockCount=r['stock_count'],
            )
            for r in rows
        ]

    def get_intraday(self, stock_id: str) -> list[IntradayPoint]:
        meta = self._repo.get_intraday_meta(stock_id)
        if meta is None:
            raise HTTPException(status_code=404, detail='Stock not found')
        try:
            points = self._repo.fetch_yahoo_intraday(stock_id, meta['market'])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f'Failed to fetch: {e}')
        if not points:
            raise HTTPException(status_code=404, detail='No intraday data')
        return [IntradayPoint(**p) for p in points]
```

- [ ] **Step 8: Create `backend/routers/__init__.py`**

```python
```
(empty file)

- [ ] **Step 9: Create `backend/routers/stocks.py`**

```python
from fastapi import APIRouter, Depends
from backend.services.stock import StockService
from backend.schemas import (
    StockSummary, StockSearchResult, StockDetail,
    TopicSummary, IntradayPoint
)

router = APIRouter(prefix='/api/stocks', tags=['stocks'])


def _svc() -> StockService:
    return StockService()


@router.get('/prices', response_model=list[StockSummary])
def get_stock_prices(ids: str = '', svc: StockService = Depends(_svc)):
    codes = [c.strip() for c in ids.split(',') if c.strip()]
    return svc.get_prices(codes)


@router.get('/search', response_model=list[StockSearchResult])
def search_stocks(q: str = '', svc: StockService = Depends(_svc)):
    return svc.search(q)


@router.get('/{stock_id}/topics', response_model=list[TopicSummary])
def get_stock_topics(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_topics(stock_id)


@router.get('/{stock_id}/intraday', response_model=list[IntradayPoint])
def get_intraday(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_intraday(stock_id)


@router.get('/{stock_id}', response_model=StockDetail)
def get_stock(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_stock(stock_id)
```

- [ ] **Step 10: Temporarily wire stocks router into main.py to validate**

In `backend/main.py`, add after the existing imports/middleware (keep existing routes for now):

```python
from backend.routers import stocks as stocks_router
app.include_router(stocks_router.router)
```

- [ ] **Step 11: Run backend tests**

```bash
python -m pytest tests/test_backend.py -v -k "stock"
```

Expected: same pass/fail as baseline. Fix any regressions before continuing.

- [ ] **Step 12: Commit**

```bash
git add backend/repositories/__init__.py backend/repositories/stock.py \
        backend/services/__init__.py backend/services/stock.py \
        backend/routers/__init__.py backend/routers/stocks.py \
        tests/test_stock_repo.py backend/main.py
git commit -m "feat(backend): add Stock repository, service, and router"
```

---

## Task 4: Market Repository + Service + Router

**Files:**
- Create: `backend/repositories/market.py`
- Create: `backend/services/market.py`
- Create: `backend/routers/market.py`

- [ ] **Step 1: Create `backend/repositories/market.py`**

```python
import sqlite3
from backend.database import get_connection, DB_PATH, DB_CHAIN_PATH

SORT_MAP = {
    'volume':   'volume DESC',
    'turnover': '(close_price * volume) DESC',
    'price':    'close_price DESC',
    'gain':     'CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) DESC',
    'loss':     'CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) ASC',
}

MARKET_MAP = {
    'listed': 'TWSE_LISTED',
    'otc':    'TPEX_OTC',
}


class MarketRepository:
    def __init__(self, db_path: str = DB_PATH, chain_path: str = DB_CHAIN_PATH):
        self._db = db_path
        self._chain = chain_path

    @staticmethod
    def _type_filter(stock_type: str) -> str:
        if stock_type == 'etf':
            return "AND stock_code LIKE '0%'"
        if stock_type == 'stock':
            return "AND stock_code NOT LIKE '0%'"
        return ''

    @staticmethod
    def _sort_expr(sort: str, order: str) -> str:
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        col = ('volume' if sort == 'volume'
               else 'CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)')
        return f'{col} {dir_}'

    def get_hot(self, sort: str, market: str, stock_type: str,
                limit: int) -> list[sqlite3.Row]:
        order = SORT_MAP.get(sort, SORT_MAP['volume'])
        mkt = MARKET_MAP.get(market, 'TWSE_LISTED')
        filter_ = self._type_filter(stock_type)
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE market = ? AND close_price IS NOT NULL AND volume > 0
                      {filter_}
                    ORDER BY {order} LIMIT ?''',
                (mkt, limit),
            ).fetchall()

    def get_search_hot(self, stock_type: str, limit: int) -> list[sqlite3.Row]:
        filter_ = self._type_filter(stock_type)
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct
                    FROM tw_stock_list
                    WHERE market = 'TWSE_LISTED' AND close_price IS NOT NULL AND volume > 0
                      {filter_}
                    ORDER BY ABS(CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)) DESC
                    LIMIT ?''',
                (limit,),
            ).fetchall()

    def get_recurring(self, limit: int) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                '''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                   FROM tw_stock_list
                   WHERE stock_code LIKE '0%'
                     AND close_price IS NOT NULL AND volume > 0
                   ORDER BY volume DESC LIMIT ?''',
                (limit,),
            ).fetchall()

    def get_sectors(self, market: str, sort: str, order: str) -> list[sqlite3.Row]:
        mkt = MARKET_MAP.get(market, 'TWSE_LISTED')
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        col = 'total_vol' if sort == 'volume' else 'avg_chg'
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT industry_name,
                           COUNT(*) AS total,
                           AVG(CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)) AS avg_chg,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) > 0
                               THEN 1 ELSE 0 END) AS up,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) < 0
                               THEN 1 ELSE 0 END) AS dn,
                           SUM(volume) AS total_vol
                    FROM tw_stock_list
                    WHERE market = ? AND close_price IS NOT NULL
                      AND change_pct IS NOT NULL AND change_pct != ""
                      AND stock_code NOT LIKE "0%"
                      AND industry_name IS NOT NULL AND industry_name != ""
                      AND industry_name NOT IN ("其他", "存託憑證")
                    GROUP BY industry_name
                    ORDER BY {col} {dir_}''',
                (mkt,),
            ).fetchall()

    def get_sector_stocks(self, name: str, sort: str, order: str) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE industry_name = ? AND close_price IS NOT NULL AND volume > 0
                      AND stock_code NOT LIKE "0%"
                    ORDER BY {self._sort_expr(sort, order)}''',
                (name,),
            ).fetchall()

    def get_chain_codes(self, name: str) -> list[str]:
        try:
            with get_connection(self._chain) as conn:
                rows = conn.execute(
                    'SELECT DISTINCT stock_code FROM tpex_industry_chain WHERE chain_topic = ?',
                    (name,),
                ).fetchall()
            return [r['stock_code'] for r in rows]
        except Exception:
            return []

    def get_stocks_by_codes(self, codes: list[str], sort: str,
                            order: str) -> list[sqlite3.Row]:
        if not codes:
            return []
        ph = ','.join('?' * len(codes))
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE stock_code IN ({ph})
                      AND close_price IS NOT NULL AND volume > 0
                    ORDER BY {self._sort_expr(sort, order)}''',
                codes,
            ).fetchall()
```

- [ ] **Step 2: Create `backend/services/market.py`**

```python
from backend.repositories.market import MarketRepository
from backend.schemas import StockSummary, RankedStock, SectorSummary


def _parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace('+', '').replace('%', ''))
    except ValueError:
        return 0.0


def _parse_volume(val) -> int:
    if val is None:
        return 0
    try:
        return int(float(str(val)))
    except ValueError:
        return 0


def _to_stock_summary(r) -> StockSummary:
    return StockSummary(
        id=r['stock_code'],
        name=r['stock_name'],
        price=float(r['close_price']) if r['close_price'] else 0.0,
        change=_parse_float(r['change_val']),
        changePercent=_parse_float(r['change_pct']),
        volume=_parse_volume(r['volume']),
    )


class MarketService:
    def __init__(self, repo: MarketRepository | None = None):
        self._repo = repo or MarketRepository()

    def get_hot(self, sort: str = 'volume', market: str = 'listed',
                stock_type: str = 'stock', limit: int = 10) -> list[StockSummary]:
        rows = self._repo.get_hot(sort, market, stock_type, limit)
        return [_to_stock_summary(r) for r in rows]

    def get_search_hot(self, stock_type: str = 'stock',
                       limit: int = 6) -> list[dict]:
        rows = self._repo.get_search_hot(stock_type, limit)
        return [
            {
                'id':            r['stock_code'],
                'name':          r['stock_name'],
                'price':         float(r['close_price']),
                'change':        _parse_float(r['change_val']),
                'changePercent': _parse_float(r['change_pct']),
            }
            for r in rows
        ]

    def get_recurring(self, limit: int = 15) -> list[RankedStock]:
        rows = self._repo.get_recurring(limit)
        return [
            RankedStock(
                rank=i + 1,
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']),
                changePercent=_parse_float(r['change_pct']),
            )
            for i, r in enumerate(rows)
        ]

    def get_sectors(self, market: str = 'listed', sort: str = 'change',
                    order: str = 'desc') -> list[SectorSummary]:
        rows = self._repo.get_sectors(market, sort, order)
        return [
            SectorSummary(
                name=r['industry_name'],
                changePercent=round(r['avg_chg'] or 0, 2),
                advance=r['up'],
                decline=r['dn'],
                totalVolume=r['total_vol'] or 0,
            )
            for r in rows
        ]

    def get_sector_stocks(self, name: str, sort: str = 'change',
                          order: str = 'desc') -> list[StockSummary]:
        rows = self._repo.get_sector_stocks(name, sort, order)
        return [_to_stock_summary(r) for r in rows]

    def get_chain_stocks(self, name: str, sort: str = 'change',
                         order: str = 'desc') -> list[StockSummary]:
        codes = self._repo.get_chain_codes(name)
        rows = self._repo.get_stocks_by_codes(codes, sort, order)
        return [_to_stock_summary(r) for r in rows]
```

- [ ] **Step 3: Create `backend/routers/market.py`**

```python
from fastapi import APIRouter, Depends
from backend.services.market import MarketService
from backend.schemas import StockSummary, RankedStock, SectorSummary

router = APIRouter(prefix='/api/market', tags=['market'])


def _svc() -> MarketService:
    return MarketService()


@router.get('/hot', response_model=list[StockSummary])
def get_market_hot(sort: str = 'volume', market: str = 'listed',
                   stock_type: str = 'stock', limit: int = 10,
                   svc: MarketService = Depends(_svc)):
    return svc.get_hot(sort, market, stock_type, limit)


@router.get('/search_hot')
def get_search_hot(stock_type: str = 'stock', limit: int = 6,
                   svc: MarketService = Depends(_svc)):
    return svc.get_search_hot(stock_type, limit)


@router.get('/recurring/tw', response_model=list[RankedStock])
def get_recurring_tw(limit: int = 15, svc: MarketService = Depends(_svc)):
    return svc.get_recurring(limit)


@router.get('/sectors', response_model=list[SectorSummary])
def get_sectors(market: str = 'listed', sort: str = 'change',
                order: str = 'desc', svc: MarketService = Depends(_svc)):
    return svc.get_sectors(market, sort, order)


@router.get('/sector/{name}/stocks', response_model=list[StockSummary])
def get_sector_stocks(name: str, sort: str = 'change', order: str = 'desc',
                      svc: MarketService = Depends(_svc)):
    return svc.get_sector_stocks(name, sort, order)


@router.get('/chain/{name}/stocks', response_model=list[StockSummary])
def get_chain_stocks(name: str, sort: str = 'change', order: str = 'desc',
                     svc: MarketService = Depends(_svc)):
    return svc.get_chain_stocks(name, sort, order)
```

- [ ] **Step 4: Add market router to `main.py`**

```python
from backend.routers import market as market_router
app.include_router(market_router.router)
```

- [ ] **Step 5: Run market-related tests**

```bash
python -m pytest tests/test_backend.py -v -k "market or sector or hot or recurring"
```

Expected: same as baseline. Fix regressions before continuing.

- [ ] **Step 6: Commit**

```bash
git add backend/repositories/market.py backend/services/market.py \
        backend/routers/market.py backend/main.py
git commit -m "feat(backend): add Market repository, service, and router"
```

---

## Task 5: Topic Repository + Service + Router

**Files:**
- Create: `backend/repositories/topic.py`
- Create: `backend/services/topic.py`
- Create: `backend/routers/topics.py`

- [ ] **Step 1: Create `backend/repositories/topic.py`**

```python
import sqlite3
from backend.database import get_connection, DB_PATH


class TopicRepository:
    def __init__(self, db_path: str = DB_PATH):
        self._db = db_path

    def get_by_level(self, level: str) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
                'FROM nlp_topics WHERE level = ? ORDER BY total_invested DESC',
                (level,),
            ).fetchall()

    def find_medium_by_name(self, name: str) -> sqlite3.Row | None:
        with get_connection(self._db) as conn:
            row = conn.execute(
                "SELECT id FROM nlp_topics WHERE name = ? AND level = 'medium'", (name,)
            ).fetchone()
            if row is None:
                row = conn.execute(
                    "SELECT id FROM nlp_topics WHERE LOWER(name) = LOWER(?) AND level = 'medium'",
                    (name,),
                ).fetchone()
            return row

    def get_children(self, parent_id: int) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
                'FROM nlp_topics WHERE parent_id = ? ORDER BY total_invested DESC',
                (parent_id,),
            ).fetchall()

    def find_by_name_and_level(self, name: str, level: str) -> sqlite3.Row | None:
        with get_connection(self._db) as conn:
            row = conn.execute(
                'SELECT id FROM nlp_topics WHERE name = ? AND level = ?', (name, level)
            ).fetchone()
            if row is None:
                row = conn.execute(
                    'SELECT id FROM nlp_topics WHERE LOWER(name) = LOWER(?) AND level = ?',
                    (name, level),
                ).fetchone()
            return row

    _SORT_COL = {
        'invested': 'ts.total_invested',
        'change':   'CAST(REPLACE(REPLACE(s.change_pct,"+",""),"%","") AS REAL)',
        'volume':   's.volume',
        'heat':     'ts.article_count',
    }

    def get_topic_stocks(self, topic_id: int, sort: str,
                         order: str) -> list[sqlite3.Row]:
        sort_col = self._SORT_COL.get(sort, self._SORT_COL['heat'])
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT s.stock_code, s.stock_name, s.close_price,
                           s.change_val, s.change_pct, s.volume,
                           ts.article_count, ts.total_invested
                    FROM nlp_topic_stocks ts
                    JOIN tw_stock_list s ON s.stock_code = ts.stock_code
                    WHERE ts.topic_id = ? AND s.close_price IS NOT NULL
                    ORDER BY {sort_col} {dir_}''',
                (topic_id,),
            ).fetchall()
```

- [ ] **Step 2: Create `backend/services/topic.py`**

```python
from fastapi import HTTPException
from backend.repositories.topic import TopicRepository
from backend.schemas import TopicSummary, TopicStock


def _parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace('+', '').replace('%', ''))
    except ValueError:
        return 0.0


def _parse_volume(val) -> int:
    if val is None:
        return 0
    try:
        return int(float(str(val)))
    except ValueError:
        return 0


def _to_topic_summary(r) -> TopicSummary:
    return TopicSummary(
        id=r['id'],
        name=r['name'],
        level=r['level'],
        parentId=r['parent_id'],
        totalInvested=r['total_invested'],
        articleCount=r['article_count'],
        stockCount=r['stock_count'],
    )


class TopicService:
    def __init__(self, repo: TopicRepository | None = None):
        self._repo = repo or TopicRepository()

    def get_topics(self, level: str = 'medium') -> list[TopicSummary]:
        if level not in ('medium', 'fine'):
            raise HTTPException(status_code=400, detail='level must be medium or fine')
        return [_to_topic_summary(r) for r in self._repo.get_by_level(level)]

    def get_children(self, name: str) -> list[TopicSummary]:
        parent = self._repo.find_medium_by_name(name)
        if parent is None:
            raise HTTPException(status_code=404, detail=f'Topic "{name}" not found')
        return [_to_topic_summary(r) for r in self._repo.get_children(parent['id'])]

    def get_topic_stocks(self, name: str, level: str = 'medium',
                         sort: str = 'heat', order: str = 'desc') -> list[TopicStock]:
        if level not in ('medium', 'fine'):
            raise HTTPException(status_code=400, detail='level must be medium or fine')
        topic = self._repo.find_by_name_and_level(name, level)
        if topic is None:
            raise HTTPException(status_code=404,
                                detail=f'Topic "{name}" not found at level {level}')
        rows = self._repo.get_topic_stocks(topic['id'], sort, order)
        return [
            TopicStock(
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']),
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
                volume=_parse_volume(r['volume']),
                articleCount=r['article_count'],
                topicInvested=r['total_invested'],
            )
            for r in rows
        ]
```

- [ ] **Step 3: Create `backend/routers/topics.py`**

```python
from fastapi import APIRouter, Depends
from backend.services.topic import TopicService
from backend.schemas import TopicSummary, TopicStock

router = APIRouter(prefix='/api/topics', tags=['topics'])


def _svc() -> TopicService:
    return TopicService()


@router.get('', response_model=list[TopicSummary])
def get_topics(level: str = 'medium', svc: TopicService = Depends(_svc)):
    return svc.get_topics(level)


@router.get('/{name}/children', response_model=list[TopicSummary])
def get_topic_children(name: str, svc: TopicService = Depends(_svc)):
    return svc.get_children(name)


@router.get('/{name}/stocks', response_model=list[TopicStock])
def get_topic_stocks(name: str, level: str = 'medium',
                     sort: str = 'heat', order: str = 'desc',
                     svc: TopicService = Depends(_svc)):
    return svc.get_topic_stocks(name, level, sort, order)
```

- [ ] **Step 4: Add topics router to `main.py`**

```python
from backend.routers import topics as topics_router
app.include_router(topics_router.router)
```

- [ ] **Step 5: Run topic tests**

```bash
python -m pytest tests/test_topics_api.py -v
```

Expected: same as baseline.

- [ ] **Step 6: Commit**

```bash
git add backend/repositories/topic.py backend/services/topic.py \
        backend/routers/topics.py backend/main.py
git commit -m "feat(backend): add Topic repository, service, and router"
```

---

## Task 6: Industry Repository + Service + Router

**Files:**
- Create: `backend/repositories/industry.py`
- Create: `backend/services/industry.py`
- Create: `backend/routers/industries.py`

- [ ] **Step 1: Create `backend/repositories/industry.py`**

```python
import sqlite3
from collections import defaultdict
from backend.database import get_connection, DB_PATH, DB_CHAIN_PATH


class IndustryRepository:
    def __init__(self, db_path: str = DB_PATH, chain_path: str = DB_CHAIN_PATH):
        self._db = db_path
        self._chain = chain_path

    @staticmethod
    def _sort_expr(sort: str, order: str) -> str:
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        col = ('volume' if sort == 'volume'
               else 'CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)')
        return f'{col} {dir_}'

    def get_industries(self, sort: str, order: str) -> tuple[list[sqlite3.Row], dict[str, list[str]]]:
        """Returns (rows, industry_codes_map)."""
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        col = {'volume': 'total_vol', 'invested': 'total_invested'}.get(sort, 'avg_chg')
        with get_connection(self._db) as conn:
            rows = conn.execute(
                f'''SELECT industry_name,
                           AVG(CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)) AS avg_chg,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) > 0
                               THEN 1 ELSE 0 END) AS up,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) < 0
                               THEN 1 ELSE 0 END) AS dn,
                           SUM(COALESCE(volume, 0)) AS total_vol,
                           COALESCE(SUM(ts.total_invested), 0) AS total_invested,
                           GROUP_CONCAT(t.stock_code) AS codes
                    FROM tw_stock_list t
                    LEFT JOIN nlp_topic_stocks ts ON t.stock_code = ts.stock_code
                    WHERE t.close_price IS NOT NULL
                      AND t.change_pct IS NOT NULL AND t.change_pct != ""
                      AND t.industry_name IS NOT NULL AND t.industry_name != ""
                      AND t.stock_code NOT LIKE "0%"
                    GROUP BY t.industry_name
                    ORDER BY {col} {dir_}''',
            ).fetchall()
        industry_codes = {
            r['industry_name']: r['codes'].split(',') if r['codes'] else []
            for r in rows
        }
        return rows, industry_codes

    def get_nlp_counts(self, all_codes: list[str],
                       industry_codes: dict[str, list[str]]) -> dict[str, int]:
        if not all_codes:
            return {}
        counts: dict[str, int] = defaultdict(int)
        try:
            ph = ','.join('?' * len(all_codes))
            with get_connection(self._db) as conn:
                nlp_rows = conn.execute(
                    f'''SELECT DISTINCT s.stock_code, s.topic_id
                        FROM nlp_topic_stocks s
                        JOIN nlp_topics t ON t.id = s.topic_id
                        WHERE t.level = 'fine' AND s.stock_code IN ({ph})''',
                    all_codes,
                ).fetchall()
            code_to_nlp: dict[str, set] = defaultdict(set)
            for nr in nlp_rows:
                code_to_nlp[nr['stock_code']].add(nr['topic_id'])
            for industry, codes in industry_codes.items():
                topics: set = set()
                for c in codes:
                    topics |= code_to_nlp.get(c, set())
                counts[industry] = len(topics)
        except Exception:
            pass
        return counts

    def get_chain_counts(self, all_codes: list[str],
                         industry_codes: dict[str, list[str]]) -> dict[str, int]:
        if not all_codes:
            return {}
        counts: dict[str, int] = defaultdict(int)
        try:
            ph = ','.join('?' * len(all_codes))
            with get_connection(self._chain) as conn:
                chain_rows = conn.execute(
                    f'SELECT stock_code, chain_topic FROM tpex_industry_chain WHERE stock_code IN ({ph})',
                    all_codes,
                ).fetchall()
            code_to_chain: dict[str, set] = defaultdict(set)
            for cr in chain_rows:
                code_to_chain[cr['stock_code']].add(cr['chain_topic'])
            for industry, codes in industry_codes.items():
                topics: set = set()
                for c in codes:
                    topics |= code_to_chain.get(c, set())
                counts[industry] = len(topics)
        except Exception:
            pass
        return counts

    def get_industry_stocks(self, name: str, sort: str,
                            order: str) -> list[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE industry_name = ? AND close_price IS NOT NULL AND volume > 0
                      AND stock_code NOT LIKE "0%"
                    ORDER BY {self._sort_expr(sort, order)}''',
                (name,),
            ).fetchall()

    def get_industry_stock_codes(self, name: str) -> list[str]:
        with get_connection(self._db) as conn:
            rows = conn.execute(
                '''SELECT stock_code FROM tw_stock_list
                   WHERE industry_name = ? AND close_price IS NOT NULL
                   AND stock_code NOT LIKE "0%"''',
                (name,),
            ).fetchall()
        return [r['stock_code'] for r in rows]

    def get_nlp_topics_for_codes(self, codes: list[str]) -> list[sqlite3.Row]:
        if not codes:
            return []
        ph = ','.join('?' * len(codes))
        try:
            with get_connection(self._db) as conn:
                return conn.execute(
                    f'''SELECT DISTINCT t.id, t.name, t.stock_count
                        FROM nlp_topics t
                        JOIN nlp_topic_stocks ns ON t.id = ns.topic_id
                        WHERE t.level = "fine" AND ns.stock_code IN ({ph})''',
                    codes,
                ).fetchall()
        except Exception:
            return []

    def get_nlp_stock_map(self, topic_ids: list[int]) -> dict[int, set]:
        if not topic_ids:
            return {}
        ph = ','.join('?' * len(topic_ids))
        with get_connection(self._db) as conn:
            rows = conn.execute(
                f'SELECT topic_id, stock_code FROM nlp_topic_stocks WHERE topic_id IN ({ph})',
                topic_ids,
            ).fetchall()
        result: dict[int, set] = defaultdict(set)
        for r in rows:
            result[r['topic_id']].add(r['stock_code'])
        return result

    def get_price_map(self, codes: list[str]) -> dict[str, float]:
        if not codes:
            return {}
        ph = ','.join('?' * len(codes))
        with get_connection(self._db) as conn:
            rows = conn.execute(
                f'''SELECT stock_code,
                           CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) AS chg
                    FROM tw_stock_list
                    WHERE stock_code IN ({ph})
                      AND change_pct IS NOT NULL AND change_pct != ""''',
                codes,
            ).fetchall()
        return {r['stock_code']: r['chg'] for r in rows}

    def get_chain_topics_for_codes(self, codes: list[str]) -> dict[str, set]:
        if not codes:
            return {}
        try:
            ph = ','.join('?' * len(codes))
            with get_connection(self._chain) as conn:
                rows = conn.execute(
                    f'SELECT chain_topic, stock_code FROM tpex_industry_chain WHERE stock_code IN ({ph})',
                    codes,
                ).fetchall()
            result: dict[str, set] = defaultdict(set)
            for r in rows:
                result[r['chain_topic']].add(r['stock_code'])
            return result
        except Exception:
            return {}
```

- [ ] **Step 2: Create `backend/services/industry.py`**

```python
from backend.repositories.industry import IndustryRepository
from backend.schemas import StockSummary, IndustrySummary, IndustryTopic


def _parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace('+', '').replace('%', ''))
    except ValueError:
        return 0.0


def _parse_volume(val) -> int:
    if val is None:
        return 0
    try:
        return int(float(str(val)))
    except ValueError:
        return 0


class IndustryService:
    def __init__(self, repo: IndustryRepository | None = None):
        self._repo = repo or IndustryRepository()

    def get_industries(self, sort: str = 'change',
                       order: str = 'desc') -> list[IndustrySummary]:
        rows, industry_codes = self._repo.get_industries(sort, order)
        all_codes = list({c for codes in industry_codes.values() for c in codes})
        nlp_counts = self._repo.get_nlp_counts(all_codes, industry_codes)
        chain_counts = self._repo.get_chain_counts(all_codes, industry_codes)
        return [
            IndustrySummary(
                name=r['industry_name'],
                topicCount=chain_counts.get(r['industry_name'], 0)
                           + nlp_counts.get(r['industry_name'], 0),
                advance=r['up'],
                decline=r['dn'],
                changePercent=round(r['avg_chg'] or 0, 2),
                totalVolume=r['total_vol'] or 0,
                totalInvested=r['total_invested'] or 0,
            )
            for r in rows
        ]

    def get_industry_stocks(self, name: str, sort: str = 'change',
                            order: str = 'desc') -> list[StockSummary]:
        rows = self._repo.get_industry_stocks(name, sort, order)
        return [
            StockSummary(
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']) if r['close_price'] else 0.0,
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
                volume=_parse_volume(r['volume']),
            )
            for r in rows
        ]

    def get_industry_topics(self, name: str) -> list[IndustryTopic]:
        industry_codes = self._repo.get_industry_stock_codes(name)
        if not industry_codes:
            return []

        nlp_rows = self._repo.get_nlp_topics_for_codes(industry_codes)
        nlp_names = {r['id']: r['name'] for r in nlp_rows}
        nlp_stock_cnt = {r['id']: r['stock_count'] for r in nlp_rows}
        nlp_stock_map = self._repo.get_nlp_stock_map(list(nlp_names.keys()))

        all_price_codes = list(
            set(industry_codes) | {c for s in nlp_stock_map.values() for c in s}
        )
        price_map = self._repo.get_price_map(all_price_codes)
        chain_topics = self._repo.get_chain_topics_for_codes(industry_codes)

        results: list[IndustryTopic] = []

        for chain_topic, codes in chain_topics.items():
            changes = [price_map[c] for c in codes if c in price_map]
            avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
            results.append(IndustryTopic(
                name=chain_topic,
                source='tpex',
                changePercent=avg_chg,
                stockCount=len(codes),
            ))

        for tid, tname in nlp_names.items():
            codes = nlp_stock_map.get(tid, set())
            changes = [price_map[c] for c in codes if c in price_map]
            avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
            results.append(IndustryTopic(
                name=tname,
                source='nlp',
                changePercent=avg_chg,
                stockCount=nlp_stock_cnt.get(tid, len(codes)),
            ))

        results.sort(key=lambda x: abs(x.changePercent), reverse=True)
        return results
```

- [ ] **Step 3: Create `backend/routers/industries.py`**

```python
from fastapi import APIRouter, Depends
from backend.services.industry import IndustryService
from backend.schemas import IndustrySummary, StockSummary, IndustryTopic

router = APIRouter(prefix='/api/market', tags=['industries'])


def _svc() -> IndustryService:
    return IndustryService()


@router.get('/industries', response_model=list[IndustrySummary])
def get_industries(sort: str = 'change', order: str = 'desc',
                   svc: IndustryService = Depends(_svc)):
    return svc.get_industries(sort, order)


@router.get('/industry/{name}/stocks', response_model=list[StockSummary])
def get_industry_stocks(name: str, sort: str = 'change', order: str = 'desc',
                        svc: IndustryService = Depends(_svc)):
    return svc.get_industry_stocks(name, sort, order)


@router.get('/industry/{name}/topics', response_model=list[IndustryTopic])
def get_industry_topics(name: str, svc: IndustryService = Depends(_svc)):
    return svc.get_industry_topics(name)
```

- [ ] **Step 4: Add industries router to `main.py`**

```python
from backend.routers import industries as industries_router
app.include_router(industries_router.router)
```

- [ ] **Step 5: Run industry tests**

```bash
python -m pytest tests/test_industries_api.py -v
```

Expected: same as baseline.

- [ ] **Step 6: Commit**

```bash
git add backend/repositories/industry.py backend/services/industry.py \
        backend/routers/industries.py backend/main.py
git commit -m "feat(backend): add Industry repository, service, and router"
```

---

## Task 7: Replace `main.py` with thin version

**Files:**
- Modify: `backend/main.py` (full replacement)

- [ ] **Step 1: Replace `backend/main.py` entirely**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import stocks, market, topics, industries

app = FastAPI(title="TopicMap TW")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(market.router)
app.include_router(topics.router)
app.include_router(industries.router)
```

- [ ] **Step 2: Run all tests**

```bash
python -m pytest tests/test_backend.py tests/test_industries_api.py tests/test_topics_api.py -v
```

Expected: identical pass/fail to Task 1 baseline. Fix any regressions.

- [ ] **Step 3: Start the server and verify manually**

```bash
uvicorn backend.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` — all 17 routes should be visible and grouped by tag.

Test a few endpoints:
```bash
curl http://localhost:8000/api/market/hot | python -m json.tool | head -20
curl http://localhost:8000/api/topics?level=medium | python -m json.tool | head -10
curl http://localhost:8000/api/market/industries | python -m json.tool | head -10
```

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "refactor(backend): replace main.py with thin router assembly"
```

---

## Task 8: Final cleanup and PR

- [ ] **Step 1: Run the full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all tests that passed in Task 1 still pass.

- [ ] **Step 2: Verify file structure**

```bash
find backend/ -name "*.py" | sort
```

Expected:
```
backend/__init__.py
backend/database.py
backend/main.py
backend/repositories/__init__.py
backend/repositories/industry.py
backend/repositories/market.py
backend/repositories/stock.py
backend/repositories/topic.py
backend/routers/__init__.py
backend/routers/industries.py
backend/routers/market.py
backend/routers/stocks.py
backend/routers/topics.py
backend/schemas.py
backend/services/__init__.py
backend/services/industry.py
backend/services/market.py
backend/services/stock.py
backend/services/topic.py
```

- [ ] **Step 3: Push and open PR**

```bash
git push origin wayne-dev
gh pr create --title "refactor(backend): Router/Service/Repository OOP architecture" \
  --body "Splits 835-line main.py into layered OOP: 4 routers, 4 services, 4 repositories, Pydantic schemas. All API paths and response shapes preserved."
```
