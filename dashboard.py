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
    if stock_stats is None:
        return []
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
    if topic_heat is None or topic_heat.empty:
        return go.Figure()
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


def _load_data() -> None:
    global _topic_heat, _topic_stats, _stock_stats
    articles     = load_articles()
    prices       = load_prices()
    _topic_heat  = compute_topic_heat(articles)
    _topic_stats = compute_topic_price(articles, prices)
    _stock_stats = compute_stock_stats(articles, prices)


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

    n_topics  = int(th["label_fine"].nunique()) if th is not None else 0
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
                _kpi_card("NLP 監控主題", str(n_topics),  "細層分群主題數"),
                _kpi_card("追蹤個股",      str(n_stocks),  "有效配對股票"),
                _kpi_card("分析文章",       str(n_articles),"語料庫總篇數"),
                _kpi_card("市場均漲跌",     avg_str,        "追蹤個股均值", avg_color),
                html.Div([
                    html.Div("已篩選主題", style={"fontSize": "10px", "color": _TXT_SEC,
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
                _chart_card("主題熱度排行",
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

            # Table
            _chart_card("個股主題明細",
                dash_table.DataTable(
                    id="stock-table",
                    columns=[
                        {"name": "代碼",     "id": "stock_id"},
                        {"name": "名稱",     "id": "stock_name"},
                        {"name": "細層主題", "id": "label_fine"},
                        {"name": "中層主題", "id": "label_medium"},
                        {"name": "文章數",   "id": "article_count"},
                        {"name": "漲跌幅",   "id": "change_pct_str"},
                        {"name": "", "id": "change_pct_float"},
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
                "CATHAY SECURITIES CORP. · 概念股監控系統 · EventCorr AI Pipeline · 僅供內部研究參考，不構成投資建議",
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
app.layout = _build_layout   # 傳函式（不加括號），Dash 每次連線時呼叫


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
    Output("stock-table",   "data"),
    Output("filter-badge",  "children"),
    Input("selected-topic", "data"),
)
def sync_charts(selected_topic):
    heat_fig    = build_heat_figure(_topic_heat, selected_topic)
    scatter_fig = build_scatter_figure(_topic_stats, selected_topic)
    table_data  = filter_stock_table(_stock_stats, selected_topic)

    badge = f"{selected_topic}  ×" if selected_topic else "（未篩選）"

    return heat_fig, scatter_fig, table_data, badge


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    _load_data()

    def _open():
        import time
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8050")

    threading.Thread(target=_open, daemon=True).start()
    print("[啟動] http://127.0.0.1:8050  （Ctrl-C 停止）")
    app.run(debug=False, host="127.0.0.1", port=8050)


if __name__ == "__main__":
    main()
