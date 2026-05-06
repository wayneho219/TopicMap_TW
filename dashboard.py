# dashboard.py
import sys
import sqlite3
import webbrowser
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_PATH = BASE_DIR / "output" / "result_all.csv"
DB_PATH = BASE_DIR / "data" / "tw_stock_list.sqlite3"
OUTPUT_PATH = BASE_DIR / "output" / "dashboard.html"

_C = dict(
    navy_deep   = "#060E1F",
    navy_dark   = "#0A1628",
    navy_card   = "#0F2040",
    navy_border = "#1E3A5F",
    gold        = "#C9A84C",
    gold_light  = "#E8C97A",
    text_pri    = "#E8EDF5",
    text_sec    = "#8A9BB5",
    up          = "#2ECC71",
    down        = "#E74C3C",
)


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


# ── Chart theme ───────────────────────────────────────────────────────────────

def _cathay_layout(fig: go.Figure, height: int = 450) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=_C["navy_card"],
        plot_bgcolor=_C["navy_dark"],
        height=height,
        font=dict(
            color=_C["text_pri"],
            family="'Noto Sans TC','Microsoft JhengHei',Arial,sans-serif",
            size=12,
        ),
        title=None,
        margin=dict(l=16, r=16, t=14, b=14),
        xaxis=dict(
            gridcolor=_C["navy_border"],
            zerolinecolor=_C["navy_border"],
            tickfont=dict(color=_C["text_sec"], size=11),
            title_font=dict(color=_C["text_sec"]),
        ),
        yaxis=dict(
            gridcolor=_C["navy_border"],
            zerolinecolor=_C["navy_border"],
            tickfont=dict(color=_C["text_sec"], size=11),
            title_font=dict(color=_C["text_sec"]),
        ),
        hoverlabel=dict(
            bgcolor="#162340",
            bordercolor=_C["gold"],
            font=dict(color=_C["text_pri"]),
        ),
    )
    return fig


# ── Chart builders ────────────────────────────────────────────────────────────

def build_heat_chart(topic_heat: pd.DataFrame) -> go.Figure:
    counts = topic_heat["article_count"].tolist()
    fig = go.Figure(go.Bar(
        x=counts,
        y=topic_heat["label_fine"],
        orientation="h",
        marker=dict(
            color=counts,
            colorscale=[
                [0.0, "#1E3A5F"],
                [0.45, "#2E6BC4"],
                [0.75, "#8060B0"],
                [1.0,  _C["gold"]],
            ],
            showscale=False,
            line=dict(width=0),
        ),
        text=counts,
        textposition="outside",
        textfont=dict(color=_C["gold"], size=11),
        hovertemplate="<b>%{y}</b><br>篇數：%{x}<extra></extra>",
    ))
    h = max(380, len(topic_heat) * 30)
    fig.update_layout(
        xaxis_title="文章篇數",
        yaxis={"categoryorder": "total ascending"},
        margin={"l": 230, "r": 80, "t": 14, "b": 30},
    )
    return _cathay_layout(fig, height=h)


def build_scatter_chart(topic_stats: pd.DataFrame) -> go.Figure:
    pct = topic_stats["avg_change_pct"].tolist()
    fig = go.Figure(go.Scatter(
        x=topic_stats["article_count"],
        y=pct,
        mode="markers+text",
        text=topic_stats["label_fine"],
        textposition="top center",
        textfont=dict(color=_C["text_sec"], size=10),
        marker=dict(
            size=(topic_stats["stock_count"].clip(upper=50) + 8).tolist(),
            color=pct,
            colorscale=[[0, _C["down"]], [0.5, "#8A9BB5"], [1, _C["up"]]],
            showscale=True,
            colorbar=dict(
                title=dict(text="均漲跌%", font=dict(color=_C["text_sec"], size=11)),
                tickfont=dict(color=_C["text_sec"], size=10),
                outlinecolor=_C["navy_border"],
                bgcolor=_C["navy_card"],
                thickness=12,
            ),
            line=dict(color=_C["gold"], width=0.8),
        ),
        hovertemplate=(
            "<b>%{text}</b><br>熱度：%{x} 篇<br>均漲跌：%{y:.2f}%<extra></extra>"
        ),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=_C["text_sec"],
                  opacity=0.4, line_width=1)
    fig.update_layout(
        xaxis_title="文章篇數（熱度）",
        yaxis_title="主題均漲跌幅 (%)",
    )
    return _cathay_layout(fig, height=480)


def build_table_chart(stock_stats: pd.DataFrame) -> go.Figure:
    pct_vals = stock_stats["change_pct_float"].tolist()
    pct_display = stock_stats["change_pct_float"].apply(
        lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
    )
    pct_font_colors = [
        _C["up"] if v > 0 else _C["down"] if v < 0 else _C["text_sec"]
        for v in pct_vals
    ]
    pct_bg = [
        "rgba(46,204,113,0.18)" if v > 0
        else "rgba(231,76,60,0.18)" if v < 0
        else _C["navy_dark"]
        for v in pct_vals
    ]
    row_bg = [
        _C["navy_dark"] if i % 2 == 0 else "#0D1E38"
        for i in range(len(stock_stats))
    ]

    fig = go.Figure(go.Table(
        columnwidth=[70, 90, 180, 150, 70, 80],
        header=dict(
            values=["代碼", "名稱", "細層主題", "中層主題", "文章數", "漲跌幅"],
            fill_color=_C["gold"],
            font=dict(color=_C["navy_deep"], size=12,
                      family="'Noto Sans TC',Arial,sans-serif"),
            align="center",
            height=38,
        ),
        cells=dict(
            values=[
                stock_stats["stock_id"].tolist(),
                stock_stats["stock_name"].tolist(),
                stock_stats["label_fine"].tolist(),
                stock_stats["label_medium"].tolist(),
                stock_stats["article_count"].tolist(),
                pct_display.tolist(),
            ],
            fill_color=[row_bg, row_bg, row_bg, row_bg, row_bg, pct_bg],
            font=dict(
                color=[_C["text_pri"]] * 5 + [pct_font_colors],
                size=12,
                family="'Noto Sans TC',Arial,sans-serif",
            ),
            align=["center", "left", "left", "left", "center", "center"],
            height=34,
        ),
    ))
    fig.update_layout(
        paper_bgcolor=_C["navy_card"],
        margin=dict(l=8, r=8, t=8, b=8),
        height=560,
    )
    return fig


# ── HTML template ─────────────────────────────────────────────────────────────

def build_dashboard(
    heat_fig: go.Figure,
    scatter_fig: go.Figure,
    table_fig: go.Figure,
    *,
    topic_count: int,
    stock_count: int,
    article_count: int,
    avg_change: float,
) -> str:
    today = datetime.now().strftime("%Y/%m/%d %H:%M")
    avg_str = f"+{avg_change:.2f}%" if avg_change >= 0 else f"{avg_change:.2f}%"
    avg_cls = "up" if avg_change > 0 else ("down" if avg_change < 0 else "")

    cfg = {"displayModeBar": False, "responsive": True}
    heat_html    = pio.to_html(heat_fig,    include_plotlyjs="cdn",  full_html=False, config=cfg)
    scatter_html = pio.to_html(scatter_fig, include_plotlyjs=False,  full_html=False, config=cfg)
    table_html   = pio.to_html(table_fig,   include_plotlyjs=False,  full_html=False, config=cfg)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>國泰證券 ─ 概念股監控儀表板</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;900&family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
  --navy-deep:  {_C['navy_deep']};
  --navy-dark:  {_C['navy_dark']};
  --navy-card:  {_C['navy_card']};
  --navy-bd:    {_C['navy_border']};
  --gold:       {_C['gold']};
  --gold-light: {_C['gold_light']};
  --txt:        {_C['text_pri']};
  --txt-sec:    {_C['text_sec']};
  --up:         {_C['up']};
  --down:       {_C['down']};
}}
*,*::before,*::after {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}

body {{
  font-family:'Noto Sans TC','Microsoft JhengHei',Arial,sans-serif;
  background:var(--navy-deep);
  color:var(--txt);
  min-height:100vh;
}}
body::before {{
  content:'';
  position:fixed; inset:0;
  background-image:
    linear-gradient(rgba(30,58,95,.10) 1px,transparent 1px),
    linear-gradient(90deg,rgba(30,58,95,.10) 1px,transparent 1px);
  background-size:52px 52px;
  pointer-events:none; z-index:0;
}}

/* ── Nav ─────────────────────── */
.nav {{
  position:sticky; top:0; z-index:100;
  background:rgba(6,14,31,.97);
  backdrop-filter:blur(16px);
  border-bottom:1px solid var(--gold);
  padding:0 36px; height:60px;
  display:flex; align-items:center; justify-content:space-between;
}}
.nav-left {{ display:flex; align-items:center; gap:14px; }}
.nav-emblem {{
  width:38px; height:38px; flex-shrink:0;
  background:var(--gold);
  clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display:flex; align-items:center; justify-content:center;
  font-family:'Noto Serif TC',serif;
  font-weight:900; font-size:16px;
  color:var(--navy-deep);
}}
.nav-brand {{ font-family:'Noto Serif TC',serif; font-size:17px; font-weight:600; color:var(--gold); letter-spacing:.06em; }}
.nav-en    {{ font-size:10px; color:rgba(201,168,76,.45); letter-spacing:.18em; font-weight:300; }}
.nav-sep   {{ width:1px; height:28px; background:var(--navy-bd); }}
.nav-mod   {{ font-size:13px; color:var(--txt-sec); letter-spacing:.06em; }}
.live-wrap {{ display:flex; align-items:center; gap:7px; font-size:12px; color:var(--txt-sec); }}
.live-dot  {{
  width:7px; height:7px; border-radius:50%;
  background:var(--up);
  animation:blink 2.4s ease-in-out infinite;
}}
@keyframes blink {{
  0%,100% {{ opacity:1; box-shadow:0 0 5px var(--up); }}
  50%     {{ opacity:.3; box-shadow:none; }}
}}

/* ── Main ────────────────────── */
.main {{
  position:relative; z-index:1;
  padding:28px 36px 44px;
  max-width:1680px; margin:0 auto;
}}

/* ── Page header ─────────────── */
.ph {{
  margin-bottom:26px;
  display:flex; align-items:flex-end; justify-content:space-between;
}}
.ph-title {{
  font-family:'Noto Serif TC',serif;
  font-size:26px; font-weight:600;
  color:var(--txt); letter-spacing:.03em;
}}
.ph-title em {{ font-style:normal; color:var(--gold); }}
.ph-desc {{ font-size:11px; color:var(--txt-sec); letter-spacing:.12em; padding-bottom:2px; }}

/* ── KPI row ─────────────────── */
.kpi-row {{
  display:grid; grid-template-columns:repeat(4,1fr);
  gap:14px; margin-bottom:18px;
}}
.kpi {{
  background:var(--navy-card);
  border:1px solid var(--navy-bd);
  border-radius:6px; padding:18px 22px;
  position:relative; overflow:hidden;
  transition:border-color .2s, transform .2s;
}}
.kpi::after {{
  content:'';
  position:absolute; top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg,var(--gold) 0%,transparent 65%);
}}
.kpi:hover {{ border-color:rgba(201,168,76,.5); transform:translateY(-2px); }}
.kpi-lbl  {{ font-size:10px; color:var(--txt-sec); letter-spacing:.14em; text-transform:uppercase; margin-bottom:10px; }}
.kpi-val  {{
  font-family:'Noto Serif TC',serif;
  font-size:34px; font-weight:600; line-height:1;
  color:var(--gold); margin-bottom:5px;
  font-variant-numeric:tabular-nums;
}}
.kpi-val.up   {{ color:var(--up);   }}
.kpi-val.down {{ color:var(--down); }}
.kpi-sub  {{ font-size:11px; color:rgba(138,155,181,.55); }}

/* ── Charts ──────────────────── */
.charts-top {{
  display:grid; grid-template-columns:1fr 1fr;
  gap:16px; margin-bottom:16px;
}}
.cc {{
  background:var(--navy-card);
  border:1px solid var(--navy-bd);
  border-radius:6px; overflow:hidden;
}}
.cc.full {{ grid-column:1/-1; }}
.cc-head {{
  padding:13px 18px;
  border-bottom:1px solid var(--navy-bd);
  display:flex; align-items:center; gap:9px;
}}
.cc-bar  {{ width:3px; height:14px; background:var(--gold); border-radius:2px; }}
.cc-ttl  {{
  font-family:'Noto Serif TC',serif;
  font-size:13px; font-weight:600;
  color:var(--gold); letter-spacing:.06em;
}}
.cc-body {{ padding:2px; }}

/* ── Footer ──────────────────── */
.footer {{
  margin-top:26px; padding-top:16px;
  border-top:1px solid var(--navy-bd);
  display:flex; justify-content:space-between; align-items:center;
  font-size:10px; color:rgba(74,96,128,.65); letter-spacing:.1em;
}}
.footer-brand {{ color:rgba(201,168,76,.4); font-weight:500; }}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-left">
    <div class="nav-emblem">國</div>
    <div>
      <div class="nav-brand">國泰證券</div>
      <div class="nav-en">CATHAY SECURITIES CORP.</div>
    </div>
    <div class="nav-sep"></div>
    <div class="nav-mod">概念股監控系統</div>
  </div>
  <div class="live-wrap">
    <span class="live-dot"></span>資料更新 · {today}
  </div>
</nav>

<div class="main">

  <div class="ph">
    <h1 class="ph-title">概念股<em>監控儀表板</em></h1>
    <p class="ph-desc">THEMATIC STOCK INTELLIGENCE · AI-POWERED EVENT CORRELATION</p>
  </div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="kpi-lbl">NLP 監控主題</div>
      <div class="kpi-val">{topic_count}</div>
      <div class="kpi-sub">細層分群主題數</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">追蹤個股</div>
      <div class="kpi-val">{stock_count}</div>
      <div class="kpi-sub">有效配對股票</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">分析文章</div>
      <div class="kpi-val">{article_count}</div>
      <div class="kpi-sub">語料庫總篇數</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">市場均漲跌</div>
      <div class="kpi-val {avg_cls}">{avg_str}</div>
      <div class="kpi-sub">追蹤個股均值</div>
    </div>
  </div>

  <div class="charts-top">
    <div class="cc">
      <div class="cc-head"><div class="cc-bar"></div><div class="cc-ttl">主題熱度排行</div></div>
      <div class="cc-body">{heat_html}</div>
    </div>
    <div class="cc">
      <div class="cc-head"><div class="cc-bar"></div><div class="cc-ttl">熱度 × 漲跌幅分析</div></div>
      <div class="cc-body">{scatter_html}</div>
    </div>
  </div>

  <div class="cc full">
    <div class="cc-head"><div class="cc-bar"></div><div class="cc-ttl">個股主題明細</div></div>
    <div class="cc-body">{table_html}</div>
  </div>

  <div class="footer">
    <span class="footer-brand">CATHAY SECURITIES CORP.</span>
    <span>概念股監控系統 · EventCorr AI Pipeline · 僅供內部研究參考，不構成投資建議</span>
    <span>{today}</span>
  </div>

</div>
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    articles = load_articles()
    prices   = load_prices()

    topic_heat  = compute_topic_heat(articles)
    topic_stats = compute_topic_price(articles, prices)
    stock_stats = compute_stock_stats(articles, prices)

    heat_fig    = build_heat_chart(topic_heat)
    scatter_fig = build_scatter_chart(topic_stats)
    table_fig   = build_table_chart(stock_stats)

    avg_change = float(stock_stats["change_pct_float"].mean()) if len(stock_stats) else 0.0

    html = build_dashboard(
        heat_fig, scatter_fig, table_fig,
        topic_count   = int(topic_heat["label_fine"].nunique()),
        stock_count   = int(stock_stats["stock_id"].nunique()),
        article_count = int(len(articles)),
        avg_change    = avg_change,
    )
    Path(OUTPUT_PATH).write_text(html, encoding="utf-8")
    print(f"[完成] 輸出：{OUTPUT_PATH}")
    webbrowser.open(f"file://{Path(OUTPUT_PATH).resolve()}")


if __name__ == "__main__":
    main()
