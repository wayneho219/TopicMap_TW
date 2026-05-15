# dashboard.py
import sys
import sqlite3
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, ctx
from dash import dash_table

# 啟動時載入一次，Callback 直接引用
_topic_heat:  Optional[pd.DataFrame] = None
_topic_stats: Optional[pd.DataFrame] = None
_stock_stats: Optional[pd.DataFrame] = None
_topic_timeline: Optional[pd.DataFrame] = None

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_PATH = BASE_DIR / "result_all.csv"
DB_PATH       = BASE_DIR / "data" / "tw_stock_list.sqlite3"
STOCKS_PATH   = BASE_DIR / "data" / "tw_stocks.csv"


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_articles(path: Path = ARTICLES_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        fallback = BASE_DIR / "output" / "result_all.csv"
        if fallback.exists():
            path = fallback
        else:
            print(f"[錯誤] 找不到 {path}，請先執行 Phase 2 產生 result_all.csv")
            sys.exit(1)
    df = pd.read_csv(path)
    df["stock_id"] = df["stock_id"].astype(str)

    if Path(STOCKS_PATH).exists():
        stocks = pd.read_csv(STOCKS_PATH, usecols=["stock_code", "industry_name"])
        stocks["stock_code"] = stocks["stock_code"].astype(str)
        df = df.merge(
            stocks,
            left_on="stock_id",
            right_on="stock_code",
            how="left",
            suffixes=("", "_stocks"),
        )
        if "industry_name_stocks" in df.columns:
            if "industry_name" in df.columns:
                df["industry_name"] = df["industry_name"].fillna(df["industry_name_stocks"])
                df = df.drop(columns=["industry_name_stocks"])
            else:
                df = df.rename(columns={"industry_name_stocks": "industry_name"})
        df["industry_name"] = df["industry_name"].fillna("其他")
        if "stock_code" in df.columns:
            df = df.drop(columns=["stock_code"])
    else:
        df["industry_name"] = "未知"

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
        articles.groupby("industry_name")
        .size()
        .reset_index(name="article_count")
        .sort_values("article_count", ascending=False)
    )


def compute_topic_price(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    merged = articles.merge(
        prices[["stock_code", "change_pct_float"]],
        left_on="stock_id", right_on="stock_code", how="inner",
    )
    deduped = merged.drop_duplicates(subset=["stock_id", "industry_name"])
    heat = compute_topic_heat(articles)
    stats = (
        deduped.groupby("industry_name")
        .agg(avg_change_pct=("change_pct_float", "mean"),
             stock_count=("stock_id", "nunique"))
        .reset_index()
    )
    return stats.merge(heat, on="industry_name", how="left")


def compute_stock_stats(articles: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    counts = (
        articles.groupby(["stock_id", "industry_name"])
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


def compute_topic_timeline(articles: pd.DataFrame) -> pd.DataFrame:
    timeline = articles.copy()
    timeline["ArticleCreateTime"] = pd.to_datetime(
        timeline["ArticleCreateTime"], errors="coerce"
    )
    timeline = timeline.dropna(subset=["ArticleCreateTime"]).copy()
    timeline["week_start"] = timeline["ArticleCreateTime"].dt.to_period("W-MON").dt.start_time
    return (
        timeline.groupby(["industry_name", "week_start"])
        .size()
        .reset_index(name="article_count")
        .sort_values(["week_start", "article_count"], ascending=[True, False])
    )


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
    if stock_stats is None:
        return []
    df = stock_stats.copy()
    if selected_topic:
        df = df[df["industry_name"] == selected_topic]
    df["change_pct_str"] = df["change_pct_float"].apply(
        lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
    )
    return df.to_dict("records")


def build_heat_figure(
    topic_heat: pd.DataFrame,
    selected: Optional[str] = None,
) -> go.Figure:
    if topic_heat is None or topic_heat.empty:
        return go.Figure()
    labels = topic_heat["industry_name"].tolist()
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
    if topic_stats is None or topic_stats.empty:
        return go.Figure()
    fig = go.Figure()

    if selected is None:
        pct = topic_stats["avg_change_pct"].tolist()
        colors = [_UP if v >= 0 else _DOWN for v in pct]
        fig.add_trace(go.Scatter(
            x=topic_stats["article_count"],
            y=pct,
            mode="markers+text",
            text=topic_stats["industry_name"],
            textposition="top center",
            textfont=dict(color=_TXT_SEC, size=10, family=_FONT),
            customdata=topic_stats["industry_name"],
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
        others = topic_stats[topic_stats["industry_name"] != selected]
        sel    = topic_stats[topic_stats["industry_name"] == selected]

        if len(others):
            fig.add_trace(go.Scatter(
                x=others["article_count"],
                y=others["avg_change_pct"],
                mode="markers",
                customdata=others["industry_name"],
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
                text=sel["industry_name"],
                textposition="top center",
                textfont=dict(color=_TXT, size=11, family=_FONT),
                customdata=sel["industry_name"],
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
        yaxis=dict(title="產業均漲跌幅 (%)", gridcolor=_GREEN_BRD,
                   zerolinecolor=_GREEN_BRD, tickfont=dict(color=_TXT_SEC)),
        hoverlabel=dict(bgcolor=_GREEN_LIGHT, bordercolor=_GREEN,
                        font=dict(color=_TXT)),
    )
    return fig


def build_timeline_figure(
    timeline_df: pd.DataFrame,
    selected: Optional[str] = None,
    top_k: int = 6,
) -> go.Figure:
    if timeline_df is None or timeline_df.empty:
        return go.Figure()

    source = timeline_df.copy()
    totals = (
        source.groupby("industry_name")["article_count"]
        .sum()
        .sort_values(ascending=False)
    )
    if selected is None:
        industries = totals.head(top_k).index.tolist()
    else:
        industries = totals.index.tolist()

    source = source[source["industry_name"].isin(industries)].copy()

    fig = go.Figure()
    for industry in industries:
        ind_df = source[source["industry_name"] == industry].sort_values("week_start")
        if ind_df.empty:
            continue

        if selected is None:
            opacity = 0.95
            width = 2
            color = _GREEN
        else:
            is_selected = industry == selected
            opacity = 1.0 if is_selected else 0.18
            width = 3 if is_selected else 1.5
            color = _GREEN if is_selected else _TXT_SEC

        fig.add_trace(go.Scatter(
            x=ind_df["week_start"],
            y=ind_df["article_count"],
            mode="lines+markers",
            name=industry,
            customdata=[industry] * len(ind_df),
            line=dict(color=color, width=width),
            marker=dict(size=6),
            opacity=opacity,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "週起始：%{x|%Y-%m-%d}<br>"
                "篇數：%{y}<extra></extra>"
            ),
            showlegend=True,
        ))

    fig.update_layout(
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        height=360,
        font=dict(family=_FONT, color=_TXT, size=12),
        margin=dict(l=16, r=16, t=10, b=16),
        title=None,
        xaxis=dict(
            title="週起始日期",
            gridcolor=_GREEN_BRD,
            zerolinecolor=_GREEN_BRD,
            tickfont=dict(color=_TXT_SEC),
        ),
        yaxis=dict(
            title="文章篇數",
            gridcolor=_GREEN_BRD,
            zerolinecolor=_GREEN_BRD,
            tickfont=dict(color=_TXT_SEC),
        ),
        hoverlabel=dict(bgcolor=_GREEN_LIGHT, bordercolor=_GREEN, font=dict(color=_TXT)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10, color=_TXT_SEC),
        ),
    )
    return fig


def _load_data() -> None:
    global _topic_heat, _topic_stats, _stock_stats, _topic_timeline
    articles     = load_articles()
    prices       = load_prices()
    _topic_heat  = compute_topic_heat(articles)
    _topic_stats = compute_topic_price(articles, prices)
    _stock_stats = compute_stock_stats(articles, prices)
    _topic_timeline = compute_topic_timeline(articles)


def _kpi_card(label: str, value: str, sub: str,
              accent: str = _GREEN) -> html.Div:
    return html.Div([
        html.Div(label, style={"fontSize": "10px", "color": _TXT_SEC,
                               "textTransform": "uppercase",
                               "letterSpacing": "0.12em", "marginBottom": "10px"}),
        html.Div(value, style={"fontSize": "28px", "fontWeight": "700",
                               "color": accent, "lineHeight": "1",
                               "marginBottom": "5px",
                               "fontVariantNumeric": "tabular-nums"}),
        html.Div(sub,   style={"fontSize": "11px", "color": "rgba(136,136,136,.6)"}),
    ], style={
        "background":   _CARD,
        "border":       f"1px solid {_GREEN_BRD}",
        "borderLeft":   f"3px solid {accent}",
        "borderRadius": "4px",
        "padding":      "16px 20px",
        "transition":   "transform .15s",
    })


def _chart_card(title: str, *children) -> html.Div:
    return html.Div([
        html.Div([
            html.Div(style={"width": "3px", "height": "14px",
                            "background": _GREEN, "borderRadius": "2px"}),
            html.Span(title, style={"fontWeight": "600", "color": _TXT,
                                    "fontSize": "13px", "letterSpacing": "0.05em"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "8px",
                  "padding": "12px 16px",
                  "borderBottom": f"1px solid {_GREEN_BRD}"}),
        html.Div(list(children), style={"padding": "2px"}),
    ], style={
        "background":   _CARD,
        "border":       f"1px solid {_GREEN_BRD}",
        "borderRadius": "4px",
        "overflow":     "hidden",
    })


def _build_layout() -> html.Div:
    th = _topic_heat
    ss = _stock_stats

    avg = float(ss["change_pct_float"].mean()) if ss is not None and len(ss) else 0.0
    avg_str   = f"+{avg:.2f}%" if avg >= 0 else f"{avg:.2f}%"
    avg_color = _UP if avg >= 0 else _DOWN

    n_topics  = int(th["industry_name"].nunique()) if th is not None else 0
    n_stocks  = int(ss["stock_id"].nunique())   if ss is not None else 0
    n_articles= int(th["article_count"].sum())  if th is not None else 0

    NAV_STYLE = {
        "background": _CARD,
        "borderBottom": f"3px solid {_GREEN}",
        "padding": "0 32px",
        "height": "60px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "position": "sticky",
        "top": "0",
        "zIndex": "100",
    }

    return html.Div([
        dcc.Store(id="selected-topic", data=None),

        # ── Nav ────────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div(style={"width": "4px", "height": "22px",
                                "background": _GREEN, "borderRadius": "2px"}),
                html.Span("國泰證券", style={"color": _GREEN, "fontWeight": "700",
                                            "fontSize": "17px", "letterSpacing": "0.06em"}),
                html.Span("｜ 概念股監控系統",
                          style={"color": _TXT_SEC, "fontSize": "12px", "marginLeft": "10px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
            html.Div([
                html.Span("● 即時",
                          style={"background": _GREEN, "color": "#fff",
                                 "fontSize": "10px", "padding": "3px 10px",
                                 "borderRadius": "12px"}),
            ]),
        ], style=NAV_STYLE),

        # ── Main ───────────────────────────────────────────────────────────
        html.Div([

            # KPI row
            html.Div([
                _kpi_card("追蹤產業", str(n_topics), "產業分類數"),
                _kpi_card("追蹤個股",      str(n_stocks),  "有效配對股票"),
                _kpi_card("分析文章",       str(n_articles),"語料庫總篇數"),
                _kpi_card("市場均漲跌",     avg_str,        "追蹤個股均值", avg_color),
                html.Div([
                    html.Div("已篩選產業", style={"fontSize": "10px", "color": _TXT_SEC,
                                                  "textTransform": "uppercase",
                                                  "letterSpacing": "0.12em",
                                                  "marginBottom": "10px"}),
                    html.Div(id="filter-badge",
                             style={"fontSize": "13px", "fontWeight": "600",
                                    "color": _GREEN, "lineHeight": "1.3"}),
                ], style={
                    "background": _CARD,
                    "border":     f"1px solid {_GREEN_BRD}",
                    "borderLeft": f"3px solid {_GREEN}",
                    "borderRadius": "4px",
                    "padding": "16px 20px",
                }),
            ], style={"display": "grid",
                      "gridTemplateColumns": "repeat(5,1fr)",
                      "gap": "12px", "marginBottom": "16px"}),

            # Charts top row
            html.Div([
                _chart_card("產業熱度排行",
                            dcc.Graph(id="heat-chart",
                                      figure=build_heat_figure(th),
                                      config={"displayModeBar": False},
                                      style={"height": "100%"})),
                _chart_card("熱度 × 漲跌幅分析",
                            dcc.Graph(id="scatter-chart",
                                      figure=build_scatter_figure(_topic_stats),
                                      config={"displayModeBar": False})),
            ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                      "gap": "14px", "marginBottom": "14px"}),

            _chart_card("產業熱度時間軸（週）",
                        dcc.Graph(id="timeline-chart",
                                  figure=build_timeline_figure(_topic_timeline),
                                  config={"displayModeBar": False})),

            # Table
            _chart_card("個股產業明細",
                dash_table.DataTable(
                    id="stock-table",
                    columns=[
                        {"name": "代碼",   "id": "stock_id"},
                        {"name": "名稱",   "id": "stock_name"},
                        {"name": "產業",   "id": "industry_name"},
                        {"name": "文章數", "id": "article_count"},
                        {"name": "漲跌幅", "id": "change_pct_str"},
                        {"name": "",       "id": "change_pct_float"},
                    ],
                    hidden_columns=["change_pct_float"],
                    data=filter_stock_table(ss, None),
                    page_size=25,
                    sort_action="native",
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": _GREEN,
                        "color": "#fff",
                        "fontWeight": "600",
                        "fontSize": "12px",
                        "fontFamily": _FONT,
                        "border": f"1px solid {_GREEN_BRD}",
                        "padding": "10px 12px",
                    },
                    style_cell={
                        "fontFamily": _FONT,
                        "fontSize": "12px",
                        "padding": "8px 12px",
                        "border": f"1px solid {_GREEN_BRD}",
                        "backgroundColor": _CARD,
                        "color": _TXT,
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"},
                         "backgroundColor": _BG},
                        {"if": {"filter_query": "{change_pct_float} > 0",
                                "column_id": "change_pct_str"},
                         "color": _UP, "fontWeight": "600"},
                        {"if": {"filter_query": "{change_pct_float} < 0",
                                "column_id": "change_pct_str"},
                         "color": _DOWN, "fontWeight": "600"},
                    ],
                ),
            ),

            # Footer
            html.Div(
                "CATHAY SECURITIES CORP. · 概念股監控系統 · TopicMap TW · 僅供內部研究參考，不構成投資建議",
                style={"textAlign": "center", "fontSize": "10px",
                       "color": "rgba(136,136,136,.5)",
                       "letterSpacing": "0.1em",
                       "marginTop": "20px",
                       "paddingTop": "16px",
                       "borderTop": f"1px solid {_GREEN_BRD}"},
            ),

        ], style={"padding": "24px 32px 36px", "maxWidth": "1680px", "margin": "0 auto"}),

    ], style={"fontFamily": _FONT, "background": _BG, "minHeight": "100vh"})


# ── Dash app ──────────────────────────────────────────────────────────────────

app = Dash(__name__, title="國泰證券 · 概念股監控")


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("selected-topic", "data"),
    Input("heat-chart",    "clickData"),
    Input("scatter-chart", "clickData"),
    State("selected-topic", "data"),
    prevent_initial_call=True,
)
def update_selected_topic(heat_click, scatter_click, current):
    triggered = ctx.triggered_id

    if triggered == "heat-chart" and heat_click:
        clicked = heat_click["points"][0]["customdata"]
        return None if clicked == current else clicked

    if triggered == "scatter-chart" and scatter_click:
        clicked = scatter_click["points"][0]["customdata"]
        return None if clicked == current else clicked

    return current


@app.callback(
    Output("heat-chart",    "figure"),
    Output("scatter-chart", "figure"),
    Output("timeline-chart", "figure"),
    Output("stock-table",   "data"),
    Output("filter-badge",  "children"),
    Input("selected-topic", "data"),
)
def sync_charts(selected_topic):
    heat_fig    = build_heat_figure(_topic_heat, selected_topic)
    scatter_fig = build_scatter_figure(_topic_stats, selected_topic)
    timeline_fig = build_timeline_figure(_topic_timeline, selected_topic)
    table_data  = filter_stock_table(_stock_stats, selected_topic)

    badge = f"{selected_topic}  ×" if selected_topic else "（未篩選）"

    return heat_fig, scatter_fig, timeline_fig, table_data, badge


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    _load_data()
    app.layout = _build_layout   # 資料已載入後再指定 layout

    def _open():
        import socket, time
        for _ in range(30):
            try:
                socket.create_connection(("127.0.0.1", 8050), timeout=0.3).close()
                break
            except OSError:
                time.sleep(0.2)
        webbrowser.open("http://127.0.0.1:8050")

    threading.Thread(target=_open, daemon=True).start()
    print("[啟動] http://127.0.0.1:8050  （Ctrl-C 停止）")
    app.run(debug=False, host="127.0.0.1", port=8050)


if __name__ == "__main__":
    main()
