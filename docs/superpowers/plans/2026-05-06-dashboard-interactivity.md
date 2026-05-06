# Dashboard 互動化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 `dashboard.py` 從靜態 HTML 輸出改寫為 Dash 應用，實作國泰證券白底綠色主題與跨圖表聯動篩選（Feature A）。

**Architecture:** 資料在啟動時載入一次存為模組層級變數；Callback 接收 `dcc.Store` 中的 `selected-topic` 字串，重新著色 Bar / Scatter 圖並篩選 DataTable，不重算原始資料。

**Tech Stack:** `dash>=2.16`（含 `dash.html`, `dash.dcc`, `dash.dash_table`）、`plotly>=5`、`pandas`、`pytest`

---

## 檔案結構

| 路徑 | 異動 |
|---|---|
| `requirements.txt` | 新增 `dash>=2.16,<3` |
| `dashboard.py` | 完整改寫：移除 `build_dashboard()` / `pio.to_html()`，改為 Dash layout + callbacks |
| `tests/test_dashboard.py` | 新建：測試三個純函式 `filter_stock_table`, `build_heat_figure`, `build_scatter_figure` |

`load_articles`, `load_prices`, `compute_topic_heat`, `compute_topic_price`, `compute_stock_stats` **不動**，直接沿用。

---

## Task 1：新增 Dash 依賴並驗證安裝

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1：在 `requirements.txt` 中加入 dash**

  在 `plotly>=5,<7` 那行下方插入：
  ```
  dash>=2.16,<3
  ```

- [ ] **Step 2：安裝**

  ```bash
  pip install "dash>=2.16,<3"
  ```

  預期輸出：`Successfully installed dash-2.x.x ...`

- [ ] **Step 3：確認 import 正常**

  ```bash
  python -c "import dash; from dash import html, dcc, dash_table, Input, Output, State, ctx; print(dash.__version__)"
  ```

  預期輸出：`2.x.x`（無 ImportError）

- [ ] **Step 4：Commit**

  ```bash
  git add requirements.txt
  git commit -m "chore: add dash dependency for interactive dashboard"
  ```

---

## Task 2：建立測試檔並寫失敗測試

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_dashboard.py`

- [ ] **Step 1：建立 tests 目錄**

  ```bash
  mkdir -p tests
  touch tests/__init__.py
  ```

- [ ] **Step 2：建立測試檔（三個測試，此時全部 ImportError / fail）**

  建立 `tests/test_dashboard.py`，內容如下：

  ```python
  import pandas as pd
  import pytest
  from plotly.graph_objects import Figure
  from dashboard import filter_stock_table, build_heat_figure, build_scatter_figure


  def _heat():
      return pd.DataFrame({
          "label_fine":    ["電子傳產", "散戶討論", "生技新藥"],
          "label_medium":  ["電子傳產", "散戶討論", "生技"],
          "article_count": [1145,       1083,        240],
      })


  def _stats():
      return pd.DataFrame({
          "label_fine":       ["電子傳產", "電子傳產", "散戶討論"],
          "label_medium":     ["電子傳產", "電子傳產", "散戶討論"],
          "article_count":    [24,          19,          45],
          "avg_change_pct":   [1.20,        -0.50,        0.80],
          "stock_count":      [8,            8,           12],
      })


  def _stocks():
      return pd.DataFrame({
          "stock_id":        ["2313", "2308", "2330"],
          "stock_name":      ["華通",  "台達電", "台積電"],
          "label_fine":      ["電子傳產", "電子傳產", "散戶討論"],
          "label_medium":    ["電子傳產", "電子傳產", "散戶討論"],
          "article_count":   [24, 19, 45],
          "change_pct_float": [-1.20, 2.35, 0.80],
      })


  # ── filter_stock_table ────────────────────────────────────────────────────────

  def test_filter_no_selection_returns_all():
      records = filter_stock_table(_stocks(), None)
      assert len(records) == 3

  def test_filter_with_selection_filters_rows():
      records = filter_stock_table(_stocks(), "電子傳產")
      assert len(records) == 2
      assert all(r["label_fine"] == "電子傳產" for r in records)

  def test_filter_adds_change_pct_str():
      records = filter_stock_table(_stocks(), None)
      assert "change_pct_str" in records[0]
      # 2330 台積電 +0.80%
      twse = next(r for r in records if r["stock_id"] == "2330")
      assert twse["change_pct_str"] == "+0.80%"
      # 2313 華通 -1.20%
      htc = next(r for r in records if r["stock_id"] == "2313")
      assert htc["change_pct_str"] == "-1.20%"


  # ── build_heat_figure ─────────────────────────────────────────────────────────

  def test_heat_figure_returns_plotly_figure():
      fig = build_heat_figure(_heat(), selected=None)
      assert isinstance(fig, Figure)

  def test_heat_figure_no_selection_all_full_opacity():
      fig = build_heat_figure(_heat(), selected=None)
      colors = list(fig.data[0].marker.color)
      # 所有 bar 應為完整不透明 rgba(0,112,60,1.0)
      assert all("1.0" in c for c in colors)

  def test_heat_figure_selection_dims_others():
      fig = build_heat_figure(_heat(), selected="電子傳產")
      colors = list(fig.data[0].marker.color)
      label_order = list(_heat()["label_fine"])
      sel_idx = label_order.index("電子傳產")
      # 選中列是 1.0，其他是 0.25
      assert "1.0" in colors[sel_idx]
      for i, c in enumerate(colors):
          if i != sel_idx:
              assert "0.25" in c


  # ── build_scatter_figure ──────────────────────────────────────────────────────

  def test_scatter_figure_returns_plotly_figure():
      fig = build_scatter_figure(_stats(), selected=None)
      assert isinstance(fig, Figure)

  def test_scatter_no_selection_one_trace():
      fig = build_scatter_figure(_stats(), selected=None)
      assert len(fig.data) == 1

  def test_scatter_with_selection_two_traces():
      # 選中時應有兩條 trace：dimmed group + highlighted dot
      fig = build_scatter_figure(_stats(), selected="電子傳產")
      assert len(fig.data) == 2
  ```

- [ ] **Step 3：確認測試失敗（函式尚未存在）**

  ```bash
  python -m pytest tests/test_dashboard.py -v 2>&1 | head -20
  ```

  預期：`ImportError: cannot import name 'filter_stock_table' from 'dashboard'`

---

## Task 3：實作三個純函式

**Files:**
- Modify: `dashboard.py`（在現有 `compute_*` 函式之後插入）

保留 `dashboard.py` 頂部所有 import 和 `load_*` / `compute_*` 函式不動。在 `compute_stock_stats` 之後加入以下內容，**取代** 舊的 `build_heat_chart`, `build_scatter_chart`, `build_table_chart`, `build_dashboard`, `main`。

- [ ] **Step 1：加入顏色常數**

  在 `compute_stock_stats` 函式結尾之後插入：

  ```python
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
      """將 6 位 hex 色碼轉為 rgba() 字串。"""
      h = hex_color.lstrip("#")
      r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
      return f"rgba({r},{g},{b},{alpha})"
  ```

- [ ] **Step 2：實作 `filter_stock_table`**

  ```python
  def filter_stock_table(
      stock_stats: pd.DataFrame,
      selected_topic: str | None,
  ) -> list[dict]:
      """篩選個股表格資料，加入格式化漲跌欄，回傳 DataTable records。"""
      df = stock_stats.copy()
      if selected_topic:
          df = df[df["label_fine"] == selected_topic]
      df["change_pct_str"] = df["change_pct_float"].apply(
          lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%"
      )
      return df.to_dict("records")
  ```

- [ ] **Step 3：實作 `build_heat_figure`**

  ```python
  def build_heat_figure(
      topic_heat: pd.DataFrame,
      selected: str | None = None,
  ) -> go.Figure:
      """熱度橫向 Bar 圖。selected 主題全色，其餘淡化至 0.25。"""
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
  ```

- [ ] **Step 4：實作 `build_scatter_figure`**

  ```python
  def build_scatter_figure(
      topic_stats: pd.DataFrame,
      selected: str | None = None,
  ) -> go.Figure:
      """熱度 × 漲跌幅散點圖。selected 主題高亮，其餘淡化。"""
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
  ```

- [ ] **Step 5：跑測試，應全部通過**

  ```bash
  python -m pytest tests/test_dashboard.py -v
  ```

  預期：11 個測試全部 PASS

- [ ] **Step 6：Commit**

  ```bash
  git add dashboard.py tests/
  git commit -m "feat: add filter_stock_table, build_heat_figure, build_scatter_figure with Cathay theme"
  ```

---

## Task 4：建立 Dash 應用骨架與 Layout

**Files:**
- Modify: `dashboard.py`（在純函式之後加入 Dash app 定義與 layout）

- [ ] **Step 1：在 `dashboard.py` 頂部加入 Dash import**

  在現有 import 區塊最後加入：

  ```python
  import threading
  import webbrowser
  from dash import Dash, html, dcc, Input, Output, State, ctx
  from dash import dash_table
  ```

  移除舊的 `import plotly.io as pio`（不再使用）。

- [ ] **Step 2：加入模組層級資料快取變數**

  在 import 之後、函式定義之前加入：

  ```python
  # 啟動時載入一次，Callback 直接引用
  _topic_heat:  pd.DataFrame | None = None
  _topic_stats: pd.DataFrame | None = None
  _stock_stats: pd.DataFrame | None = None
  ```

- [ ] **Step 3：加入 `_load_data()` 函式**

  ```python
  def _load_data() -> None:
      global _topic_heat, _topic_stats, _stock_stats
      articles     = load_articles()
      prices       = load_prices()
      _topic_heat  = compute_topic_heat(articles)
      _topic_stats = compute_topic_price(articles, prices)
      _stock_stats = compute_stock_stats(articles, prices)
  ```

- [ ] **Step 4：加入 `_kpi_card()` helper**

  ```python
  def _kpi_card(label: str, value: str, sub: str,
                accent: str = _GREEN) -> html.Div:
      """單一 KPI 卡片（白底 + 左側 3px 色條）。"""
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
  ```

- [ ] **Step 5：加入 `_build_layout()` 函式**

  ```python
  def _build_layout() -> html.Div:
      th = _topic_heat
      ss = _stock_stats

      avg = float(_stock_stats["change_pct_float"].mean()) if ss is not None and len(ss) else 0.0
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
                          # 隱藏欄位供 conditional styling 使用
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
  ```

- [ ] **Step 6：加入 `_chart_card()` helper（在 `_kpi_card` 之後）**

  ```python
  def _chart_card(title: str, *children) -> html.Div:
      """帶標題列的圖表卡片容器。"""
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
  ```

- [ ] **Step 7：確認 layout 函式無語法錯誤**

  ```bash
  python -c "
  import dashboard
  dashboard._load_data()
  layout = dashboard._build_layout()
  print('layout OK:', type(layout))
  "
  ```

  預期：`layout OK: <class 'dash.html.Div.Div'>`（無 exception）

- [ ] **Step 8：Commit**

  ```bash
  git add dashboard.py
  git commit -m "feat: add Dash layout skeleton with Cathay green-white theme"
  ```

---

## Task 5：實作 Callbacks 與 main()

**Files:**
- Modify: `dashboard.py`（在 `_build_layout` 之後加入 app 初始化與 callbacks）

- [ ] **Step 1：初始化 Dash app 物件**

  在 `_build_layout` 之後加入：

  ```python
  app = Dash(__name__, title="國泰證券 · 概念股監控")
  app.layout = _build_layout   # 傳函式，Dash 會在啟動後呼叫
  ```

  > 注意：傳入函式（不加括號）讓 Dash 在每次連線時重新呼叫 layout，以確保資料更新。

- [ ] **Step 2：實作 `update_selected_topic` callback**

  ```python
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
  ```

- [ ] **Step 3：實作 `sync_charts` callback**

  ```python
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
  ```

- [ ] **Step 4：實作 `main()`**

  ```python
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
  ```

- [ ] **Step 5：確認所有測試仍然通過**

  ```bash
  python -m pytest tests/test_dashboard.py -v
  ```

  預期：11 個測試全部 PASS

- [ ] **Step 6：Commit**

  ```bash
  git add dashboard.py
  git commit -m "feat: implement Dash callbacks for cross-chart topic filtering"
  ```

---

## Task 6：Smoke Test 與最終驗證

- [ ] **Step 1：啟動 Dash 應用**

  先確認 `output/result_all.csv` 與 `data/tw_stock_list.sqlite3` 存在（需先跑完 topic_model Phase 2）。

  ```bash
  python dashboard.py
  ```

  預期輸出：
  ```
  [啟動] http://127.0.0.1:8050  （Ctrl-C 停止）
  Dash is running on http://127.0.0.1:8050
  ```

  瀏覽器自動開啟。

- [ ] **Step 2：驗證初始畫面**

  - [ ] 導覽列：白底 + 綠色下邊線，「國泰證券」綠色字樣
  - [ ] 5 個 KPI 卡片顯示正確數字
  - [ ] 熱度排行圖：所有 bar 為深綠色
  - [ ] 散點圖：所有泡泡正常顯示
  - [ ] 個股表格：顯示全部個股，漲色綠跌色紅

- [ ] **Step 3：驗證聯動行為**

  - [ ] 點擊熱度排行中的任一 bar → 該 bar 保持全色，其餘淡化；散點圖對應泡泡放大高亮；表格只顯示該主題個股；已篩選 badge 更新
  - [ ] 點擊同一 bar 再次 → 恢復全部顯示，badge 顯示「（未篩選）」
  - [ ] 點擊散點圖泡泡 → 觸發同樣聯動效果

- [ ] **Step 4：最終 Commit**

  ```bash
  git add .
  git commit -m "feat: dashboard interactive Dash app with Cathay green-white theme and cross-chart filtering"
  ```

---

## 自我審查紀錄

- ✅ `filter_stock_table` / `build_heat_figure` / `build_scatter_figure` 均有對應測試
- ✅ `_chart_card` 在 Task 4 Step 6 定義，Task 4 Step 5 使用，順序正確
- ✅ `app.layout = _build_layout`（傳函式）確保資料已載入再建構 layout
- ✅ `customdata` 用於傳遞 label_fine，callback 從 `clickData["points"][0]["customdata"]` 讀取，與圖表定義一致
- ✅ DataTable 含隱藏欄 `change_pct_float` 供 conditional styling 判斷漲跌色
- ✅ 未實作 Feature B/C/D/E（YAGNI）
