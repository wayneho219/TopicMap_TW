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
