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
    # 解析 "+1.20%" → 1.20；過濾空白或無效值
    cleaned = df["change_pct"].str.strip().str.replace("%", "", regex=False)
    df = df[cleaned != ""].copy()
    df["change_pct_float"] = cleaned[cleaned != ""].astype(float)
    return df


def compute_topic_heat(articles: pd.DataFrame) -> pd.DataFrame:
    heat = (
        articles.groupby(["label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
        .sort_values("article_count", ascending=False)
    )
    return heat


def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    merged = articles.merge(prices[["stock_code", "change_pct_float"]],
                            left_on="stock_id", right_on="stock_code", how="inner")
    # Per-stock average: each stock counts once regardless of article count
    deduped = merged.drop_duplicates(subset=["stock_id", "label_fine"])
    heat = compute_topic_heat(articles)
    stats = (
        deduped.groupby(["label_fine", "label_medium"])
        .agg(
            avg_change_pct=("change_pct_float", "mean"),
            stock_count=("stock_id", "nunique"),
        )
        .reset_index()
    )
    stats = stats.merge(heat, on=["label_fine", "label_medium"], how="left")
    return stats


def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    # 每個 (stock_id, label_fine) 的文章數
    counts = (
        articles.groupby(["stock_id", "label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
    )
    # 取每支股票文章數最多的主題（主要主題）
    idx = counts.groupby("stock_id")["article_count"].idxmax()
    primary = counts.loc[idx].reset_index(drop=True)
    # JOIN 股價
    result = primary.merge(
        prices[["stock_code", "stock_name", "change_pct_float"]],
        left_on="stock_id", right_on="stock_code", how="inner"
    ).drop(columns=["stock_code"])
    return result.sort_values("article_count", ascending=False)


def build_heat_chart(topic_heat: pd.DataFrame) -> go.Figure:
    medium_labels = topic_heat["label_medium"].unique().tolist()
    color_map = {m: f"hsl({i * 360 // len(medium_labels)}, 60%, 55%)"
                 for i, m in enumerate(medium_labels)}
    colors = topic_heat["label_medium"].map(color_map)

    fig = go.Figure(go.Bar(
        x=topic_heat["article_count"],
        y=topic_heat["label_fine"],
        orientation="h",
        marker_color=colors,
        text=topic_heat["article_count"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>篇數：%{x}<extra></extra>",
    ))
    fig.update_layout(
        title="主題熱度排行",
        xaxis_title="文章篇數",
        yaxis={"categoryorder": "total ascending"},
        height=max(400, len(topic_heat) * 22),
        margin={"l": 200},
    )
    return fig


def build_scatter_chart(topic_stats: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=topic_stats["article_count"],
        y=topic_stats["avg_change_pct"],
        mode="markers+text",
        text=topic_stats["label_fine"],
        textposition="top center",
        marker={
            "size": (topic_stats["stock_count"].clip(upper=50) + 5).tolist(),
            "color": topic_stats["avg_change_pct"].tolist(),
            "colorscale": "RdYlGn",
            "showscale": True,
            "colorbar": {"title": "均漲跌%"},
        },
        hovertemplate=(
            "<b>%{text}</b><br>"
            "熱度：%{x} 篇<br>"
            "均漲跌：%{y:.2f}%<br>"
            "<extra></extra>"
        ),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        title="主題熱度 × 股價漲跌幅",
        xaxis_title="文章篇數（熱度）",
        yaxis_title="主題均漲跌幅 (%)",
        height=500,
    )
    return fig


def build_table_chart(stock_stats: pd.DataFrame) -> go.Figure:
    pct_display = stock_stats["change_pct_float"].apply(
        lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
    )
    fig = go.Figure(go.Table(
        header={
            "values": ["股票代碼", "股票名稱", "細層主題", "中層主題", "文章數", "漲跌幅"],
            "fill_color": "#2c3e50",
            "font": {"color": "white", "size": 13},
            "align": "center",
        },
        cells={
            "values": [
                stock_stats["stock_id"].tolist(),
                stock_stats["stock_name"].tolist(),
                stock_stats["label_fine"].tolist(),
                stock_stats["label_medium"].tolist(),
                stock_stats["article_count"].tolist(),
                pct_display.tolist(),
            ],
            "fill_color": [
                ["#f5f5f5" if i % 2 == 0 else "white" for i in range(len(stock_stats))]
            ],
            "align": ["center", "left", "left", "left", "center", "center"],
        },
    ))
    fig.update_layout(title="個股主題明細", height=500)
    return fig


def build_dashboard(heat_fig: go.Figure, scatter_fig: go.Figure, table_fig: go.Figure) -> str:
    html_parts = [
        pio.to_html(heat_fig, include_plotlyjs="cdn", full_html=False),
        pio.to_html(scatter_fig, include_plotlyjs=False, full_html=False),
        pio.to_html(table_fig, include_plotlyjs=False, full_html=False),
    ]
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<title>EventCorr 概念股監控儀表板</title>
<style>
  body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
  h1 {{ color: #2c3e50; }}
  .chart {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
<h1>EventCorr 概念股監控儀表板</h1>
<div class="chart">{html_parts[0]}</div>
<div class="chart">{html_parts[1]}</div>
<div class="chart">{html_parts[2]}</div>
</body>
</html>"""


def main():
    articles = load_articles()
    prices = load_prices()

    topic_heat = compute_topic_heat(articles)
    topic_stats = compute_topic_price(articles, prices)
    stock_stats = compute_stock_stats(articles, prices)

    heat_fig = build_heat_chart(topic_heat)
    scatter_fig = build_scatter_chart(topic_stats)
    table_fig = build_table_chart(stock_stats)

    html = build_dashboard(heat_fig, scatter_fig, table_fig)
    Path(OUTPUT_PATH).write_text(html, encoding="utf-8")
    print(f"[完成] 輸出：{OUTPUT_PATH}")
    webbrowser.open(f"file://{Path(OUTPUT_PATH).resolve()}")


if __name__ == "__main__":
    main()
