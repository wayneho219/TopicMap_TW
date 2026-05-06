# dashboard.py
import sys
import sqlite3
import webbrowser
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_PATH = BASE_DIR / "output" / "result_all.csv"
DB_PATH = BASE_DIR / "data" / "tw_stock_list.sqlite3"
OUTPUT_PATH = BASE_DIR / "output" / "dashboard.html"


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_articles(path: Path = ARTICLES_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        print(f"[錯誤] 找不到 {path}，請先執行 Phase 2 產生 result_all.csv")
        sys.exit(1)
    df = pd.read_csv(path)
    df["stock_id"] = df["stock_id"].astype(str)
    return df


def load_prices(db_path: Path = DB_PATH) -> pd.DataFrame:
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
    latest = df["quote_date"].max()
    df = df[df["quote_date"] == latest].copy()
    df["change_pct_float"] = pd.to_numeric(
        df["change_pct"].str.strip().str.replace("%", "", regex=False),
        errors="coerce",
    )
    df = df.dropna(subset=["change_pct_float"]).copy()
    return df


# ── Compute ───────────────────────────────────────────────────────────────────

def compute_topic_heat(articles: pd.DataFrame) -> pd.DataFrame:
    return (
        articles.groupby(["label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
        .sort_values("article_count", ascending=False)
    )


def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    merged = articles.merge(
        prices[["stock_code", "change_pct_float"]],
        left_on="stock_id", right_on="stock_code", how="inner",
    )
    deduped = merged.drop_duplicates(subset=["stock_id", "label_fine"])
    heat = compute_topic_heat(articles)
    stats = (
        deduped.groupby(["label_fine", "label_medium"])
        .agg(avg_change_pct=("change_pct_float", "mean"),
             stock_count=("stock_id", "nunique"))
        .reset_index()
    )
    return stats.merge(heat, on=["label_fine", "label_medium"], how="left")


def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    counts = (
        articles.groupby(["stock_id", "label_fine", "label_medium"])
        .size()
        .reset_index(name="article_count")
    )
    idx = counts.groupby("stock_id")["article_count"].idxmax()
    primary = counts.loc[idx].reset_index(drop=True)
    result = primary.merge(
        prices[["stock_code", "stock_name", "change_pct_float"]],
        left_on="stock_id", right_on="stock_code", how="inner",
    ).drop(columns=["stock_code"])
    return result.sort_values("article_count", ascending=False)


# ── 國泰品牌色 ────────────────────────────────────────────────────────────────
_GREEN       = "#00703C"
_GREEN_LIGHT = "#E8F5EE"
_GREEN_BRD   = "#E0EDE6"
_BG          = "#FAFBFA"
_CARD        = "#FFFFFF"
_TXT         = "#1A1A1A"
_TXT_SEC     = "#888888"
_UP          = "#00703C"
_DOWN        = "#D32F2F"
_FONT        = "'Noto Sans TC','Microsoft JhengHei',sans-serif"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def filter_stock_table(
    stock_stats: pd.DataFrame,
    selected_topic: Optional[str],
) -> list[dict]:
    df = stock_stats.copy()
    if selected_topic:
        df = df[df["label_fine"] == selected_topic]
    df["change_pct_str"] = df["change_pct_float"].apply(
        lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
    )
    return df.to_dict("records")


def build_heat_figure(
    topic_heat: pd.DataFrame,
    selected: Optional[str] = None,
) -> go.Figure:
    labels = topic_heat["label_fine"].tolist()
    counts = topic_heat["article_count"].tolist()

    colors = [
        _rgba(_GREEN, 1.0) if (selected is None or l == selected)
        else _rgba(_GREEN, 0.25)
        for l in labels
    ]

    fig = go.Figure(go.Bar(
        x=counts,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=counts,
        textposition="outside",
        textfont=dict(color=_GREEN, size=11),
        customdata=labels,
        hovertemplate="<b>%{customdata}</b><br>篇數：%{x}<extra></extra>",
    ))
    h = max(380, len(topic_heat) * 30)
    fig.update_layout(
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        height=h,
        font=dict(family=_FONT, color=_TXT, size=12),
        margin=dict(l=230, r=80, t=14, b=30),
        title=None,
        xaxis=dict(
            title="文章篇數",
            gridcolor=_GREEN_BRD,
            zerolinecolor=_GREEN_BRD,
            tickfont=dict(color=_TXT_SEC, size=11),
        ),
        yaxis=dict(
            categoryorder="total ascending",
            tickfont=dict(color=_TXT, size=11),
        ),
        hoverlabel=dict(bgcolor=_GREEN_LIGHT, bordercolor=_GREEN,
                        font=dict(color=_TXT)),
    )
    return fig


def build_scatter_figure(
    topic_stats: pd.DataFrame,
    selected: Optional[str] = None,
) -> go.Figure:
    fig = go.Figure()

    if selected is None:
        pct = topic_stats["avg_change_pct"].tolist()
        colors = [_UP if v >= 0 else _DOWN for v in pct]
        fig.add_trace(go.Scatter(
            x=topic_stats["article_count"],
            y=pct,
            mode="markers+text",
            text=topic_stats["label_fine"],
            textposition="top center",
            textfont=dict(color=_TXT_SEC, size=10, family=_FONT),
            customdata=topic_stats["label_fine"],
            marker=dict(
                color=colors,
                size=(topic_stats["stock_count"].clip(upper=50) + 8).tolist(),
                line=dict(color=_GREEN_BRD, width=1),
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "熱度：%{x} 篇<br>均漲跌：%{y:.2f}%<extra></extra>"
            ),
            showlegend=False,
        ))
    else:
        others = topic_stats[topic_stats["label_fine"] != selected]
        sel    = topic_stats[topic_stats["label_fine"] == selected]

        if len(others):
            fig.add_trace(go.Scatter(
                x=others["article_count"],
                y=others["avg_change_pct"],
                mode="markers",
                customdata=others["label_fine"],
                marker=dict(color="rgba(180,180,180,0.25)", size=8),
                hovertemplate="<b>%{customdata}</b><extra></extra>",
                showlegend=False,
            ))

        if len(sel):
            pct_val = float(sel["avg_change_pct"].iloc[0])
            dot_color = _UP if pct_val >= 0 else _DOWN
            fig.add_trace(go.Scatter(
                x=sel["article_count"],
                y=sel["avg_change_pct"],
                mode="markers+text",
                text=sel["label_fine"],
                textposition="top center",
                textfont=dict(color=_TXT, size=11, family=_FONT),
                customdata=sel["label_fine"],
                marker=dict(
                    color=dot_color,
                    size=22,
                    line=dict(color="#fff", width=2.5),
                ),
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    "熱度：%{x} 篇<br>均漲跌：%{y:.2f}%<extra></extra>"
                ),
                showlegend=False,
            ))

    fig.add_hline(y=0, line_dash="dash", line_color=_TXT_SEC,
                  opacity=0.4, line_width=1)
    fig.update_layout(
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        height=480,
        font=dict(family=_FONT, color=_TXT, size=12),
        margin=dict(l=16, r=16, t=14, b=14),
        title=None,
        xaxis=dict(title="文章篇數（熱度）", gridcolor=_GREEN_BRD,
                   zerolinecolor=_GREEN_BRD, tickfont=dict(color=_TXT_SEC)),
        yaxis=dict(title="主題均漲跌幅 (%)", gridcolor=_GREEN_BRD,
                   zerolinecolor=_GREEN_BRD, tickfont=dict(color=_TXT_SEC)),
        hoverlabel=dict(bgcolor=_GREEN_LIGHT, bordercolor=_GREEN,
                        font=dict(color=_TXT)),
    )
    return fig


# ── (Tasks 4 and 5 will add layout and callbacks here) ───────────────────────
