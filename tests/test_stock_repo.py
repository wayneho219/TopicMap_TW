import sqlite3
import pytest
from backend.repositories.stock import StockRepository


def test_stock_repo_find_by_id_raises_on_no_schema():
    repo = StockRepository(':memory:')
    with pytest.raises(sqlite3.OperationalError):
        repo.find_by_id('XXXX')


@pytest.fixture
def seeded_repo(tmp_path):
    db_file = str(tmp_path / "test.sqlite3")
    conn = sqlite3.connect(db_file)
    conn.execute(
        '''CREATE TABLE tw_stock_list (
            stock_code TEXT, stock_name TEXT,
            close_price TEXT, change_val TEXT, change_pct TEXT, volume TEXT,
            market TEXT, industry_name TEXT,
            high_price TEXT, low_price TEXT, open_price TEXT
        )'''
    )
    conn.execute(
        "INSERT INTO tw_stock_list VALUES ('2330','台積電','1000','10','+1.01%','50000','TWSE_LISTED','半導體業','1010','990','995')"
    )
    conn.commit()
    conn.close()
    return StockRepository(db_file)


def test_find_by_id_returns_row(seeded_repo):
    row = seeded_repo.find_by_id('2330')
    assert row is not None
    assert row['stock_code'] == '2330'


def test_find_by_id_returns_none_for_missing(seeded_repo):
    assert seeded_repo.find_by_id('XXXX') is None


def test_search_finds_by_code(seeded_repo):
    rows = seeded_repo.search('2330')
    assert len(rows) == 1
    assert rows[0]['stock_code'] == '2330'


def test_search_finds_by_name(seeded_repo):
    rows = seeded_repo.search('台積電')
    assert len(rows) == 1


def test_get_prices_returns_empty_for_no_codes():
    repo = StockRepository(':memory:')
    assert repo.get_prices([]) == []
