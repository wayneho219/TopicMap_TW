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
