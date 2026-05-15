import sqlite3
from typing import Optional, List
from backend.database import get_connection, DB_PATH


class TopicRepository:
    def __init__(self, db_path: str = DB_PATH):
        self._db = db_path

    def get_by_level(self, level: str) -> List[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
                'FROM nlp_topics WHERE level = ? ORDER BY total_invested DESC',
                (level,),
            ).fetchall()

    def find_medium_by_name(self, name: str) -> Optional[sqlite3.Row]:
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

    def get_children(self, parent_id: int) -> List[sqlite3.Row]:
        with get_connection(self._db) as conn:
            return conn.execute(
                'SELECT id, name, level, parent_id, total_invested, article_count, stock_count '
                'FROM nlp_topics WHERE parent_id = ? ORDER BY total_invested DESC',
                (parent_id,),
            ).fetchall()

    def find_by_name_and_level(self, name: str, level: str) -> Optional[sqlite3.Row]:
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
                         order: str) -> List[sqlite3.Row]:
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
