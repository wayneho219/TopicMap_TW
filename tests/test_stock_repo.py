import sqlite3
import pytest
from backend.repositories.stock import StockRepository


def test_stock_repo_find_by_id_returns_none_for_missing():
    repo = StockRepository(':memory:')
    result = repo.find_by_id('XXXX')
    assert result is None


def test_stock_repo_search_returns_empty_for_blank():
    repo = StockRepository(':memory:')
    result = repo.search('')
    assert result == []


def test_stock_repo_get_prices_returns_empty_for_no_codes():
    repo = StockRepository(':memory:')
    result = repo.get_prices([])
    assert result == []
