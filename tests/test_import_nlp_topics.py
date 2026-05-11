# tests/test_import_nlp_topics.py
import os
import sqlite3
import textwrap
import pytest

# 讓 pytest 能 import scripts 目錄
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.import_nlp_topics import import_nlp_topics

CSV_CONTENT = textwrap.dedent("""\
    stock_id,industry_name,ArticleCreateTime,close_price,volume,invested_amount,label_medium,label_fine
    2330,半導體業,2026-03-05,1000.0,42000000,42000000000.0,AI半導體,台積電股
    2330,半導體業,2026-03-07,1020.0,38000000,38760000000.0,AI半導體,台積電股
    2454,半導體業,2026-03-05,820.0,5000000,4100000000.0,AI半導體,消費電子
    1101,水泥工業,2026-03-05,25.5,8000000,204000000.0,高股息,年度配息
""")

@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "result_all.csv"
    p.write_text(CSV_CONTENT, encoding="utf-8")
    return str(p)

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.sqlite3")

def test_creates_medium_topics(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT name FROM nlp_topics WHERE level='medium' ORDER BY name"
    ).fetchall()
    conn.close()
    assert [r[0] for r in rows] == ["AI半導體", "高股息"]

def test_creates_fine_topics_with_correct_parent(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT f.name, m.name AS parent_name
        FROM nlp_topics f
        JOIN nlp_topics m ON m.id = f.parent_id
        WHERE f.level = 'fine'
        ORDER BY f.name
    """).fetchall()
    conn.close()
    name_to_parent = {r[0]: r[1] for r in rows}
    assert name_to_parent["台積電股"] == "AI半導體"
    assert name_to_parent["消費電子"] == "AI半導體"
    assert name_to_parent["年度配息"] == "高股息"

def test_medium_total_invested(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT total_invested FROM nlp_topics WHERE name='AI半導體' AND level='medium'"
    ).fetchone()
    conn.close()
    # 42B + 38.76B + 4.1B = 84,860,000,000
    assert abs(row[0] - 84_860_000_000.0) < 1.0

def test_topic_stocks_populated(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM nlp_topic_stocks").fetchone()[0]
    conn.close()
    assert count > 0

def test_fine_stock_invested(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT ts.total_invested
        FROM nlp_topic_stocks ts
        JOIN nlp_topics t ON t.id = ts.topic_id
        WHERE t.name = '台積電股' AND t.level = 'fine' AND ts.stock_code = '2330'
    """).fetchone()
    conn.close()
    # 42B + 38.76B = 80,760,000,000
    assert abs(row[0] - 80_760_000_000.0) < 1.0

def test_idempotent(csv_path, db_path):
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    import_nlp_topics(csv_path=csv_path, db_path=db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM nlp_topics WHERE level='medium'"
    ).fetchone()[0]
    conn.close()
    assert count == 2
