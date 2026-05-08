import sqlite3
import os
import json
import datetime
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

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
