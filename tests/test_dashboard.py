import pytest
import pandas as pd
from dashboard import load_articles

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
