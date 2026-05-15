import sqlite3
from typing import List, Optional
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
                limit: int) -> List[sqlite3.Row]:
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

    def get_search_hot(self, stock_type: str, limit: int) -> List[sqlite3.Row]:
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

    def get_recurring(self, limit: int) -> List[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                '''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                   FROM tw_stock_list
                   WHERE stock_code LIKE '0%'
                     AND close_price IS NOT NULL AND volume > 0
                   ORDER BY volume DESC LIMIT ?''',
                (limit,),
            ).fetchall()

    def get_sectors(self, market: str, sort: str, order: str) -> List[sqlite3.Row]:
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

    def get_sector_stocks(self, name: str, sort: str, order: str) -> List[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE industry_name = ? AND close_price IS NOT NULL AND volume > 0
                      AND stock_code NOT LIKE "0%"
                    ORDER BY {self._sort_expr(sort, order)}''',
                (name,),
            ).fetchall()

    def get_chain_codes(self, name: str) -> List[str]:
        try:
            with get_connection(self._chain) as conn:
                rows = conn.execute(
                    'SELECT DISTINCT stock_code FROM tpex_industry_chain WHERE chain_topic = ?',
                    (name,),
                ).fetchall()
            return [r['stock_code'] for r in rows]
        except (sqlite3.OperationalError, FileNotFoundError):
            return []

    def get_stocks_by_codes(self, codes: List[str], sort: str,
                            order: str) -> List[sqlite3.Row]:
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
