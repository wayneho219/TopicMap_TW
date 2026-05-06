import pytest
import pandas as pd
import sqlite3
from dashboard import load_articles, load_prices

SAMPLE_CSV = """stock_id,industry_name,ArticleCreateTime,label_medium,label_fine
1101,水泥工業,2026-03-12,合併財務報告公告,季合併財報公告
1101,水泥工業,2026-03-11,合併財務報告公告,季合併財報公告
2330,半導體,2026-03-10,AI科技概念股,AI液冷記憶體個股
"""


def test_load_articles_columns(tmp_path):
    f = tmp_path / "articles.csv"
    f.write_text(SAMPLE_CSV)
    df = load_articles(str(f))
    assert set(["stock_id", "label_fine", "label_medium", "ArticleCreateTime"]).issubset(df.columns)


def test_load_articles_stock_id_is_str(tmp_path):
    f = tmp_path / "articles.csv"
    f.write_text(SAMPLE_CSV)
    df = load_articles(str(f))
    assert df["stock_id"].dtype == object  # string type for JOIN


def test_load_articles_missing_file():
    with pytest.raises(SystemExit):
        load_articles("nonexistent.csv")


def test_load_prices_columns(tmp_path):
    db = tmp_path / "tw_stock_list.sqlite3"
    conn = sqlite3.connect(str(db))
    conn.execute("""
        CREATE TABLE tw_stock_list (
            stock_code TEXT, stock_name TEXT, change_pct TEXT, quote_date TEXT
        )
    """)
    conn.execute("INSERT INTO tw_stock_list VALUES ('1101','台泥','+1.20%','2026-04-13')")
    conn.execute("INSERT INTO tw_stock_list VALUES ('2330','台積電','-0.50%','2026-04-13')")
    conn.commit(); conn.close()
    df = load_prices(str(db))
    assert set(["stock_code", "stock_name", "change_pct_float"]).issubset(df.columns)


def test_load_prices_change_pct_is_float(tmp_path):
    db = tmp_path / "tw_stock_list.sqlite3"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE tw_stock_list (stock_code TEXT, stock_name TEXT, change_pct TEXT, quote_date TEXT)")
    conn.execute("INSERT INTO tw_stock_list VALUES ('1101','台泥','+1.20%','2026-04-13')")
    conn.commit(); conn.close()
    df = load_prices(str(db))
    assert df["change_pct_float"].dtype == float
    assert abs(df.iloc[0]["change_pct_float"] - 1.20) < 0.01


def test_load_prices_missing_db():
    with pytest.raises(SystemExit):
        load_prices("nonexistent.sqlite3")
