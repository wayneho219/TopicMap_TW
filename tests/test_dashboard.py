import pytest
import pandas as pd
import sqlite3
from dashboard import load_articles, load_prices, compute_topic_heat, compute_topic_price

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


def _sample_articles():
    return pd.DataFrame({
        "stock_id": ["1101", "1101", "2330", "2330", "2330"],
        "label_fine": ["AI液冷", "AI液冷", "AI液冷", "航運指數", "航運指數"],
        "label_medium": ["AI科技", "AI科技", "AI科技", "航運", "航運"],
        "ArticleCreateTime": ["2026-03-10"] * 5,
    })


def _sample_prices():
    return pd.DataFrame({
        "stock_code": ["1101", "2330"],
        "stock_name": ["台泥", "台積電"],
        "change_pct_float": [1.20, -0.50],
    })


def test_compute_topic_heat_counts():
    heat = compute_topic_heat(_sample_articles())
    assert set(["label_fine", "label_medium", "article_count"]).issubset(heat.columns)
    ai_row = heat[heat["label_fine"] == "AI液冷"].iloc[0]
    assert ai_row["article_count"] == 3


def test_compute_topic_heat_sorted():
    heat = compute_topic_heat(_sample_articles())
    assert heat.iloc[0]["article_count"] >= heat.iloc[1]["article_count"]


def test_compute_topic_price_avg():
    stats = compute_topic_price(_sample_articles(), _sample_prices())
    assert set(["label_fine", "label_medium", "article_count", "avg_change_pct", "stock_count"]).issubset(stats.columns)
    ai_row = stats[stats["label_fine"] == "AI液冷"].iloc[0]
    # 1101(+1.20) and 2330(-0.50) both in AI液冷, per-stock avg = (1.20 + (-0.50)) / 2 = 0.35
    assert abs(ai_row["avg_change_pct"] - 0.35) < 0.01


def test_compute_topic_price_excludes_no_price():
    articles = _sample_articles()
    prices = pd.DataFrame({  # only 1101
        "stock_code": ["1101"], "stock_name": ["台泥"], "change_pct_float": [1.20]
    })
    stats = compute_topic_price(articles, prices)
    # 航運指數 only has 2330; 2330 has no price data → should be excluded
    assert "航運指數" not in stats["label_fine"].values
