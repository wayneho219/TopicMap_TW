# dashboard.py
import sys
import sqlite3
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

ARTICLES_PATH = "result_all.csv"
DB_PATH = "data/tw_stock_list.sqlite3"
OUTPUT_PATH = "dashboard.html"


def load_articles(path: str = ARTICLES_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        print(f"[錯誤] 找不到 {path}，請先執行 Phase 2 產生 result_all.csv")
        sys.exit(1)
    df = pd.read_csv(path)
    df["stock_id"] = df["stock_id"].astype(str)
    return df


def load_prices(db_path: str = DB_PATH) -> pd.DataFrame:
    if not Path(db_path).exists():
        print(f"[錯誤] 找不到 {db_path}，請確認資料庫路徑")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(
        "SELECT stock_code, stock_name, change_pct, quote_date "
        "FROM tw_stock_list WHERE quote_date IS NOT NULL",
        conn,
    )
    conn.close()
    # 取最新日期快照
    latest = df["quote_date"].max()
    df = df[df["quote_date"] == latest].copy()
    # 解析 "+1.20%" → 1.20
    df["change_pct_float"] = (
        df["change_pct"].str.replace("%", "", regex=False).astype(float)
    )
    return df


def compute_topic_heat(articles: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def build_heat_chart(topic_heat: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_scatter_chart(topic_stats: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_table_chart(stock_stats: pd.DataFrame) -> go.Figure:
    raise NotImplementedError


def build_dashboard(heat_fig: go.Figure, scatter_fig: go.Figure, table_fig: go.Figure) -> str:
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
