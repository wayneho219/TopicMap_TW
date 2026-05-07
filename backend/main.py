import sqlite3
import os
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

    return {
        'id': row['stock_code'],
        'name': row['stock_name'],
        'price': float(row['close_price']) if row['close_price'] is not None else 0.0,
        'change': _parse_float(row['change_val']),
        'changePercent': _parse_float(row['change_pct']),
        'volume': int(float(row['volume'])) if row['volume'] is not None else 0,
        'market': row['market'],
        'industry': row['industry_name'],
        'tags': _tags(row['market']),
        'status': '已收盤',
        'high': None,
        'low': None,
        'prevClose': None,
        'open': None,
    }
