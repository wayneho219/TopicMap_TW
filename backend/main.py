import sqlite3
import os
import json
import datetime
import urllib.request
from collections import defaultdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DB_PATH       = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')
DB_CHAIN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tpex_industry_chain.sqlite3')

MARKET_LABEL = {
    'TWSE_LISTED': '上市',
    'TPEX_OTC': '上櫃',
    'TPEX_EMERGING': '興櫃',
}

YAHOO_SUFFIX = {
    'TWSE_LISTED': '.TW',
    'TPEX_OTC': '.TWO',
    'TPEX_EMERGING': '.TWO',
}

TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))

def _tags(market: str) -> list[str]:
    label = MARKET_LABEL.get(market, market)
    if market == 'TWSE_LISTED':
        return [label, '可現沖']
    return [label]

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

SORT_MAP = {
    'volume':      'volume DESC',
    'turnover':    '(close_price * volume) DESC',
    'price':       'close_price DESC',
    'gain':        'CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) DESC',
    'loss':        'CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) ASC',
}

MARKET_MAP = {
    'listed': 'TWSE_LISTED',
    'otc':    'TPEX_OTC',
}

def _type_filter(stock_type: str) -> str:
    if stock_type == 'etf':
        return "AND stock_code LIKE '0%'"
    if stock_type == 'stock':
        return "AND stock_code NOT LIKE '0%'"
    return ""  # 'all'


@app.get('/api/market/hot')
def get_market_hot(sort: str = 'volume', market: str = 'listed',
                   stock_type: str = 'stock', limit: int = 10):
    order  = SORT_MAP.get(sort, SORT_MAP['volume'])
    mkt    = MARKET_MAP.get(market, 'TWSE_LISTED')
    filter_ = _type_filter(stock_type)
    conn   = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
            FROM tw_stock_list
            WHERE market = ? AND close_price IS NOT NULL AND volume > 0
              {filter_}
            ORDER BY {order}
            LIMIT ?
            ''',
            (mkt, limit),
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
        }
        for r in rows
    ]


@app.get('/api/market/search_hot')
def get_search_hot(stock_type: str = 'stock', limit: int = 6):
    filter_ = _type_filter(stock_type)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT stock_code, stock_name, close_price, change_val, change_pct
            FROM tw_stock_list
            WHERE market = 'TWSE_LISTED' AND close_price IS NOT NULL AND volume > 0
              {filter_}
            ORDER BY ABS(CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL)) DESC
            LIMIT ?
            ''',
            (limit,),
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
        }
        for r in rows
    ]


@app.get('/api/stocks/prices')
def get_stock_prices(ids: str = ''):
    codes = [c.strip() for c in ids.split(',') if c.strip()]
    if not codes:
        return []
    placeholders = ','.join('?' * len(codes))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
            FROM tw_stock_list
            WHERE stock_code IN ({placeholders})
            ''',
            codes,
        ).fetchall()
    finally:
        conn.close()
    order_map = {c: i for i, c in enumerate(codes)}
    result = _stock_rows_to_list(rows)
    result.sort(key=lambda x: order_map.get(x['id'], 999))
    return result


@app.get('/api/market/recurring/tw')
def get_recurring_tw(limit: int = 15):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            '''
            SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
            FROM tw_stock_list
            WHERE stock_code LIKE '0%'
              AND close_price IS NOT NULL AND volume > 0
            ORDER BY volume DESC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            'rank':          i + 1,
            'id':            r['stock_code'],
            'name':          r['stock_name'],
            'price':         float(r['close_price']),
            'changePercent': _parse_float(r['change_pct']),
        }
        for i, r in enumerate(rows)
    ]


@app.get('/api/market/sectors')
def get_sectors(market: str = 'listed', sort: str = 'change', order: str = 'desc'):
    mkt = MARKET_MAP.get(market, 'TWSE_LISTED')
    dir_ = 'ASC' if order == 'asc' else 'DESC'
    col  = 'total_vol' if sort == 'volume' else 'avg_chg'
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT industry_name,
                   COUNT(*) AS total,
                   AVG(CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL)) AS avg_chg,
                   SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) > 0 THEN 1 ELSE 0 END) AS up,
                   SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) < 0 THEN 1 ELSE 0 END) AS dn,
                   SUM(volume) AS total_vol
            FROM tw_stock_list
            WHERE market = ? AND close_price IS NOT NULL
              AND change_pct IS NOT NULL AND change_pct != ""
              AND stock_code NOT LIKE "0%"
              AND industry_name IS NOT NULL AND industry_name != ""
              AND industry_name NOT IN ("其他", "存託憑證")
            GROUP BY industry_name
            ORDER BY {col} {dir_}
            ''',
            (mkt,),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            'name':          r['industry_name'],
            'changePercent': round(r['avg_chg'] or 0, 2),
            'advance':       r['up'],
            'decline':       r['dn'],
            'totalVolume':   r['total_vol'] or 0,
        }
        for r in rows
    ]


def _stock_rows_to_list(rows) -> list[dict]:
    return [
        {
            'id':            r['stock_code'],
            'name':          r['stock_name'],
            'price':         float(r['close_price']) if r['close_price'] else 0.0,
            'change':        _parse_float(r['change_val']),
            'changePercent': _parse_float(r['change_pct']),
            'volume':        _parse_volume(r['volume']),
        }
        for r in rows
    ]


def _sort_expr(sort: str, order: str) -> str:
    dir_ = 'ASC' if order == 'asc' else 'DESC'
    col  = ('volume' if sort == 'volume'
            else f'CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)')
    return f'{col} {dir_}'


@app.get('/api/market/sector/{name}/stocks')
def get_sector_stocks(name: str, sort: str = 'change', order: str = 'desc'):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
            FROM tw_stock_list
            WHERE industry_name = ? AND close_price IS NOT NULL AND volume > 0
              AND stock_code NOT LIKE "0%"
            ORDER BY {_sort_expr(sort, order)}
            ''',
            (name,),
        ).fetchall()
    finally:
        conn.close()
    return _stock_rows_to_list(rows)


@app.get('/api/market/chain/{name}/stocks')
def get_chain_stocks(name: str, sort: str = 'change', order: str = 'desc'):
    chain_conn = sqlite3.connect(DB_CHAIN_PATH)
    chain_conn.row_factory = sqlite3.Row
    try:
        chain_rows = chain_conn.execute(
            'SELECT DISTINCT stock_code FROM tpex_industry_chain WHERE chain_topic = ?',
            (name,),
        ).fetchall()
    finally:
        chain_conn.close()

    codes = [r['stock_code'] for r in chain_rows]
    if not codes:
        return []

    placeholders = ','.join('?' * len(codes))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
            FROM tw_stock_list
            WHERE stock_code IN ({placeholders})
              AND close_price IS NOT NULL AND volume > 0
            ORDER BY {_sort_expr(sort, order)}
            ''',
            codes,
        ).fetchall()
    finally:
        conn.close()
    return _stock_rows_to_list(rows)


@app.get('/api/stocks/search')
def search_stocks(q: str = ''):
    q = q.strip()
    if not q:
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            '''
            SELECT stock_code, stock_name, market, industry_name,
                   close_price, change_val, change_pct
            FROM tw_stock_list
            WHERE stock_code LIKE ? OR stock_name LIKE ?
            ORDER BY
                CASE WHEN stock_code = ?         THEN 0
                     WHEN stock_code LIKE ?       THEN 1
                     WHEN stock_name LIKE ?       THEN 2
                     ELSE 3 END,
                stock_code
            LIMIT 30
            ''',
            (f'%{q}%', f'%{q}%', q, f'{q}%', f'{q}%'),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            'id': r['stock_code'],
            'name': r['stock_name'],
            'market': r['market'],
            'industry': r['industry_name'],
            'price': float(r['close_price']) if r['close_price'] is not None else 0.0,
            'change': _parse_float(r['change_val']),
            'changePercent': _parse_float(r['change_pct']),
        }
        for r in rows
    ]


@app.get('/api/stocks/{stock_id}/intraday')
def get_intraday(stock_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            'SELECT market, close_price, change_val FROM tw_stock_list WHERE stock_code = ?', (stock_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail='Stock not found')

    suffix = YAHOO_SUFFIX.get(row['market'], '.TW')
    symbol = f'{stock_id}{suffix}'

    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'Failed to fetch: {e}')

    result = payload.get('chart', {}).get('result')
    if not result:
        raise HTTPException(status_code=404, detail='No intraday data')

    chart = result[0]
    prev_close = chart['meta'].get('chartPreviousClose') or chart['meta'].get('previousClose') or 1.0
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


@app.get('/api/stocks/{stock_id}')
def get_stock(stock_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            'SELECT * FROM tw_stock_list WHERE stock_code = ?', (stock_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail='Stock not found')

    close = float(row['close_price']) if row['close_price'] is not None else 0.0
    change = _parse_float(row['change_val'])
    prev_close = round(close - change, 2) if close and change else None

    def _opt_float(val):
        return float(val) if val is not None else None

    return {
        'id': row['stock_code'],
        'name': row['stock_name'],
        'price': close,
        'change': change,
        'changePercent': _parse_float(row['change_pct']),
        'volume': _parse_volume(row['volume']),
        'market': row['market'],
        'industry': row['industry_name'],
        'tags': _tags(row['market']),
        'status': '已收盤',
        'high': _opt_float(row['high_price']),
        'low': _opt_float(row['low_price']),
        'prevClose': prev_close,
        'open': _opt_float(row['open_price']),
    }


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


@app.get('/api/market/industries')
def get_industries(sort: str = 'change', order: str = 'desc'):
    dir_ = 'ASC' if order == 'asc' else 'DESC'
    col  = 'total_vol' if sort == 'volume' else 'avg_chg'

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f'''
            SELECT industry_name,
                   AVG(CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL)) AS avg_chg,
                   SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) > 0
                       THEN 1 ELSE 0 END) AS up,
                   SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) < 0
                       THEN 1 ELSE 0 END) AS dn,
                   SUM(COALESCE(volume, 0)) AS total_vol,
                   GROUP_CONCAT(stock_code) AS codes
            FROM tw_stock_list
            WHERE close_price IS NOT NULL
              AND change_pct IS NOT NULL AND change_pct != ""
              AND industry_name IS NOT NULL AND industry_name != ""
              AND stock_code NOT LIKE "0%"
            GROUP BY industry_name
            ORDER BY {col} {dir_}
            ''',
        ).fetchall()

        industry_codes: dict[str, list[str]] = {
            r['industry_name']: r['codes'].split(',') if r['codes'] else []
            for r in rows
        }
        all_codes = list({c for codes in industry_codes.values() for c in codes})

        # NLP topic counts via stock overlap
        nlp_counts: dict[str, int] = defaultdict(int)
        if all_codes:
            ph = ','.join('?' * len(all_codes))
            nlp_rows = conn.execute(
                f'''SELECT s.stock_code, s.topic_id
                    FROM nlp_topic_stocks s
                    JOIN nlp_topic_industry_map m ON s.topic_id = m.topic_id
                    WHERE m.is_industry = 1 AND s.stock_code IN ({ph})''',
                all_codes,
            ).fetchall()
            code_to_nlp: dict[str, set] = defaultdict(set)
            for nr in nlp_rows:
                code_to_nlp[nr['stock_code']].add(nr['topic_id'])
            for industry, codes in industry_codes.items():
                topics: set = set()
                for c in codes:
                    topics |= code_to_nlp.get(c, set())
                nlp_counts[industry] = len(topics)
    finally:
        conn.close()

    # Chain topic counts via stock overlap (cross-DB)
    chain_counts: dict[str, int] = defaultdict(int)
    if all_codes:
        chain_conn = sqlite3.connect(DB_CHAIN_PATH)
        chain_conn.row_factory = sqlite3.Row
        try:
            ph = ','.join('?' * len(all_codes))
            chain_rows = chain_conn.execute(
                f'SELECT stock_code, chain_topic FROM tpex_industry_chain WHERE stock_code IN ({ph})',
                all_codes,
            ).fetchall()
        finally:
            chain_conn.close()

        code_to_chain: dict[str, set] = defaultdict(set)
        for cr in chain_rows:
            code_to_chain[cr['stock_code']].add(cr['chain_topic'])
        for industry, codes in industry_codes.items():
            topics = set()
            for c in codes:
                topics |= code_to_chain.get(c, set())
            chain_counts[industry] = len(topics)

    return [
        {
            'name':          r['industry_name'],
            'topicCount':    chain_counts[r['industry_name']] + nlp_counts[r['industry_name']],
            'advance':       r['up'],
            'decline':       r['dn'],
            'changePercent': round(r['avg_chg'] or 0, 2),
            'totalVolume':   r['total_vol'] or 0,
        }
        for r in rows
    ]


@app.get('/api/market/industry/{name}/topics')
def get_industry_topics(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Stocks in this industry
        industry_stocks = conn.execute(
            '''SELECT stock_code FROM tw_stock_list
               WHERE industry_name = ? AND close_price IS NOT NULL
               AND stock_code NOT LIKE "0%" ''',
            (name,),
        ).fetchall()
        industry_codes = [r['stock_code'] for r in industry_stocks]

        if not industry_codes:
            return []

        ph = ','.join('?' * len(industry_codes))

        # NLP topics with stock overlap
        nlp_rows = conn.execute(
            f'''SELECT DISTINCT t.id, t.name, t.stock_count
                FROM nlp_topics t
                JOIN nlp_topic_industry_map m ON t.id = m.topic_id
                JOIN nlp_topic_stocks ns ON t.id = ns.topic_id
                WHERE m.is_industry = 1 AND t.level = "fine"
                  AND ns.stock_code IN ({ph})''',
            industry_codes,
        ).fetchall()

        nlp_names      = {r['id']: r['name']        for r in nlp_rows}
        nlp_stock_cnt  = {r['id']: r['stock_count'] for r in nlp_rows}

        nlp_stock_map: dict[int, set] = defaultdict(set)
        if nlp_names:
            ph2 = ','.join('?' * len(nlp_names))
            for row in conn.execute(
                f'SELECT topic_id, stock_code FROM nlp_topic_stocks WHERE topic_id IN ({ph2})',
                list(nlp_names.keys()),
            ).fetchall():
                nlp_stock_map[row['topic_id']].add(row['stock_code'])

        # Price map for all relevant codes
        all_price_codes = list(
            set(industry_codes) | {c for s in nlp_stock_map.values() for c in s}
        )
        ph3 = ','.join('?' * len(all_price_codes))
        price_map = {
            r['stock_code']: r['chg']
            for r in conn.execute(
                f'''SELECT stock_code,
                           CAST(REPLACE(REPLACE(change_pct, "+", ""), "%", "") AS REAL) AS chg
                    FROM tw_stock_list
                    WHERE stock_code IN ({ph3})
                      AND change_pct IS NOT NULL AND change_pct != ""''',
                all_price_codes,
            ).fetchall()
        }
    finally:
        conn.close()

    # Chain topics via stock overlap (cross-DB)
    chain_conn = sqlite3.connect(DB_CHAIN_PATH)
    chain_conn.row_factory = sqlite3.Row
    try:
        ph = ','.join('?' * len(industry_codes))
        chain_rows = chain_conn.execute(
            f'SELECT chain_topic, stock_code FROM tpex_industry_chain WHERE stock_code IN ({ph})',
            industry_codes,
        ).fetchall()
    finally:
        chain_conn.close()

    topic_stocks: dict[str, set] = defaultdict(set)
    for r in chain_rows:
        topic_stocks[r['chain_topic']].add(r['stock_code'])

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
            'stockCount':    nlp_stock_cnt.get(tid, len(codes)),
        })

    results.sort(key=lambda x: abs(x['changePercent']), reverse=True)
    return results
