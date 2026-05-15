import sqlite3
import urllib.request
import json
import datetime
from typing import Optional
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

    def find_by_id(self, stock_id: str) -> Optional[sqlite3.Row]:
        with get_connection(self._db) as conn:
            try:
                return conn.execute(
                    'SELECT * FROM tw_stock_list WHERE stock_code = ?', (stock_id,)
                ).fetchone()
            except sqlite3.OperationalError:
                return None

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

    def get_intraday_meta(self, stock_id: str) -> Optional[sqlite3.Row]:
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
