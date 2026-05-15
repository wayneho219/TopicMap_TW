import sqlite3
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional
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

    def get_industries(self, sort: str, order: str) -> Tuple[List[sqlite3.Row], Dict[str, List[str]]]:
        """Returns (rows, industry_codes_map)."""
        dir_ = 'ASC' if order == 'asc' else 'DESC'
        col = {'volume': 'total_vol'}.get(sort, 'avg_chg')
        with get_connection(self._db) as conn:
            rows = conn.execute(
                f'''SELECT industry_name,
                           AVG(CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL)) AS avg_chg,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) > 0
                               THEN 1 ELSE 0 END) AS up,
                           SUM(CASE WHEN CAST(REPLACE(REPLACE(change_pct,"+",""),"%","") AS REAL) < 0
                               THEN 1 ELSE 0 END) AS dn,
                           SUM(COALESCE(volume, 0)) AS total_vol,
                           GROUP_CONCAT(stock_code) AS codes
                    FROM tw_stock_list
                    WHERE close_price IS NOT NULL
                      AND change_pct IS NOT NULL AND change_pct != ""
                      AND industry_name IS NOT NULL AND industry_name != ""
                      AND stock_code NOT LIKE "0%"
                    GROUP BY industry_name
                    ORDER BY {col} {dir_}''',
            ).fetchall()
        industry_codes: Dict[str, List[str]] = {
            r['industry_name']: r['codes'].split(',') if r['codes'] else []
            for r in rows
        }
        return rows, industry_codes

    def get_nlp_counts(self, all_codes: List[str],
                       industry_codes: Dict[str, List[str]]) -> Dict[str, int]:
        if not all_codes:
            return {}
        counts: Dict[str, int] = defaultdict(int)
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
            code_to_nlp: Dict[str, Set] = defaultdict(set)
            for nr in nlp_rows:
                code_to_nlp[nr['stock_code']].add(nr['topic_id'])
            for industry, codes in industry_codes.items():
                topics: Set = set()
                for c in codes:
                    topics |= code_to_nlp.get(c, set())
                counts[industry] = len(topics)
        except (sqlite3.OperationalError, FileNotFoundError):
            pass
        return counts

    def get_chain_counts(self, all_codes: List[str],
                         industry_codes: Dict[str, List[str]]) -> Dict[str, int]:
        if not all_codes:
            return {}
        counts: Dict[str, int] = defaultdict(int)
        try:
            ph = ','.join('?' * len(all_codes))
            with get_connection(self._chain) as conn:
                chain_rows = conn.execute(
                    f'SELECT stock_code, chain_topic FROM tpex_industry_chain WHERE stock_code IN ({ph})',
                    all_codes,
                ).fetchall()
            code_to_chain: Dict[str, Set] = defaultdict(set)
            for cr in chain_rows:
                code_to_chain[cr['stock_code']].add(cr['chain_topic'])
            for industry, codes in industry_codes.items():
                topics: Set = set()
                for c in codes:
                    topics |= code_to_chain.get(c, set())
                counts[industry] = len(topics)
        except (sqlite3.OperationalError, FileNotFoundError):
            pass
        return counts

    def get_industry_stocks(self, name: str, sort: str,
                            order: str) -> List[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                f'''SELECT stock_code, stock_name, close_price, change_val, change_pct, volume
                    FROM tw_stock_list
                    WHERE industry_name = ? AND close_price IS NOT NULL AND volume > 0
                      AND stock_code NOT LIKE "0%"
                    ORDER BY {self._sort_expr(sort, order)}''',
                (name,),
            ).fetchall()

    def get_industry_stock_codes(self, name: str) -> List[str]:
        with get_connection(self._db) as conn:
            rows = conn.execute(
                '''SELECT stock_code FROM tw_stock_list
                   WHERE industry_name = ? AND close_price IS NOT NULL
                   AND stock_code NOT LIKE "0%"''',
                (name,),
            ).fetchall()
        return [r['stock_code'] for r in rows]

    def get_nlp_topics_for_codes(self, codes: List[str]) -> List[sqlite3.Row]:
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
        except (sqlite3.OperationalError, FileNotFoundError):
            return []

    def get_nlp_stock_map(self, topic_ids: List[int]) -> Dict[int, Set[str]]:
        if not topic_ids:
            return {}
        ph = ','.join('?' * len(topic_ids))
        with get_connection(self._db) as conn:
            rows = conn.execute(
                f'SELECT topic_id, stock_code FROM nlp_topic_stocks WHERE topic_id IN ({ph})',
                topic_ids,
            ).fetchall()
        result: Dict[int, Set[str]] = defaultdict(set)
        for r in rows:
            result[r['topic_id']].add(r['stock_code'])
        return result

    def get_price_map(self, codes: List[str]) -> Dict[str, float]:
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

    def get_chain_topics_for_codes(self, codes: List[str]) -> Dict[str, Set[str]]:
        if not codes:
            return {}
        try:
            ph = ','.join('?' * len(codes))
            with get_connection(self._chain) as conn:
                rows = conn.execute(
                    f'SELECT chain_topic, stock_code FROM tpex_industry_chain WHERE stock_code IN ({ph})',
                    codes,
                ).fetchall()
            result: Dict[str, Set[str]] = defaultdict(set)
            for r in rows:
                result[r['chain_topic']].add(r['stock_code'])
            return result
        except (sqlite3.OperationalError, FileNotFoundError):
            return {}
