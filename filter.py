"""
PTT 版規雜訊 + 財務公告格式文過濾模組
======================================
用途：在 topic_model.py Step 1 載入 articles.csv 後，
  1. 過濾版規/論壇管理類雜訊（板規、水桶）
  2. 過濾財務公告格式文（月營收表格、財報、股利、違約交割等）
     → 只保留個股操作討論、心得分析等有實質內容的文章

使用方式：
    from filter import filter_dataframe, filter_announcements_dataframe
"""

import re
from typing import Optional

# ── 標題規則：[公告] + 版規關鍵字 ────────────────────────────────────────────
# 只匹配公告類型的版規管理文，不影響一般 [公告] 新聞
_TITLE_RULES: list[tuple[str, str]] = [
    (r"\[公告\].*水桶",     "水桶公告"),
    (r"\[公告\].*警告",     "違規警告"),
    (r"\[公告\].*自刪",     "自刪公告"),
    (r"\[公告\].*板規",     "板規公告"),
    (r"\[公告\].*違規",     "違規公告"),
    (r"\[公告\].*處份",     "處份公告"),
    (r"\[公告\].*禁言",     "禁言公告"),
]

# ── 內文規則：強信號，任一命中即為雜訊 ─────────────────────────────────────
_CONTENT_RULES: list[tuple[str, str]] = [
    (r"多人水桶公告",           "多人水桶公告"),
    (r"板主群合議認定",         "板主群合議"),
    (r"違規條目.{0,20}罰則",    "違規條目+罰則"),
    (r"罰則.{0,20}違規事證",    "罰則+違規事證"),
    (r"水桶[一二三六]{0,1}[天週月]", "水桶時間"),
    (r"板主查察板面",           "板主查察"),
]

_COMPILED_TITLE   = [(re.compile(pat), label) for pat, label in _TITLE_RULES]
_COMPILED_CONTENT = [(re.compile(pat), label) for pat, label in _CONTENT_RULES]


def is_noise(title: str, text: str) -> bool:
    """回傳 True 表示此文章為版規雜訊，應予過濾。"""
    for regex, _ in _COMPILED_TITLE:
        if regex.search(title):
            return True
    for regex, _ in _COMPILED_CONTENT:
        if regex.search(text):
            return True
    return False


def noise_reason(title: str, text: str) -> Optional[str]:
    """回傳命中的規則名稱（debug 用）；未命中回傳 None。"""
    for regex, label in _COMPILED_TITLE:
        if regex.search(title):
            return f"title:{label}"
    for regex, label in _COMPILED_CONTENT:
        if regex.search(text):
            return f"content:{label}"
    return None


def filter_dataframe(df, title_col: str = "ArticleTitle", text_col: str = "ArticleText"):
    """從 DataFrame 移除版規雜訊列，回傳 (clean_df, n_removed)。"""
    mask = df.apply(lambda r: is_noise(str(r[title_col]), str(r[text_col])), axis=1)
    n_removed = int(mask.sum())
    return df[~mask].reset_index(drop=True), n_removed


# ══════════════════════════════════════════════════════════════════════════════
# 公告格式文過濾（第二道）
# 目的：過濾結構化財務公告，保留個股操作討論與心得分析
# ══════════════════════════════════════════════════════════════════════════════

_ANNOUNCEMENT_CONTENT_RULES: list[tuple[str, str]] = [
    # 財報公告（季/年度合併財報）
    (r"提報董事會或經董事會決議日期",                               "財報公告"),
    (r"審計委員會通過日期",                                         "財報公告"),
    (r"日累計至.{1,15}日止.{0,20}期末",                            "財報公告"),

    # 月營收結構化表格（公開資訊觀測站格式）
    (r"去年同期.{0,20}增減.{0,20}百分比",                          "月營收表格"),
    (r"本月.{0,5}去年同期.{0,5}增減",                              "月營收表格"),
    (r"累計營業收入.{0,20}去年同期",                                "月營收表格"),

    # 公開資訊觀測站 / TWSE 抓取格式（標題+來源+網址+內文結構）
    (r"來源\s*(公開資訊觀測站|TWSE|證交所|臺灣證券交易所|證券櫃檯買賣中心).{0,80}網址",
                                                                    "公告scraped"),

    # 股利配發決議（結構化公告）
    (r"法定盈餘公積.{0,20}(配股|現金股利)",                        "股利決議"),
    (r"普通股.{0,10}現金股利.{0,30}盈餘公積",                      "股利決議"),

    # 股東會紀念品
    (r"股東常會紀念品",                                             "股東會紀念品"),
    (r"本次.{0,5}股東.{0,5}紀念品",                                "股東會紀念品"),

    # 違約交割
    (r"證券商申報投資人違約金額",                                   "違約交割"),
    (r"買進.{0,5}賣出.{0,5}合計總金額.{0,10}相抵",                 "違約交割"),

    # 新股申購
    (r"申購開始日.{0,20}申購截止日.{0,20}預扣款日",                "新股申購"),

    # 法人買賣超 / 周轉率排行表格
    (r"買超排行.{0,20}證券代號.{0,20}買超張數",                    "法人排行"),
    (r"股票名稱.{0,10}收盤價.{0,10}漲跌幅.{0,10}成交量.{0,10}周轉率",
                                                                    "周轉率排行"),
    (r"股票名稱.{0,10}成交.{0,10}漲跌.{0,10}投信買.{0,10}外資買", "外資投信排行"),

    # 金控月自結損益
    (r"事實發生日.{0,50}自結盈餘",                                  "金控自結"),
    (r"自結合併損益.{0,30}每股",                                    "金控自結"),

    # 勞退基金績效
    (r"勞動基金.{0,20}收益.{0,20}億元",                            "勞退基金"),

    # 注意交易資訊標準（公告格式）
    (r"有價證券於集中交易市場達公布注意交易資訊標準",              "注意交易標準"),

    # 重大投資取得／處分
    (r"最近一會計年度.{0,20}(銷售總額|進貨總額).{0,20}比例",       "取得處分"),
]

_COMPILED_ANNOUNCEMENT_CONTENT = [
    (re.compile(pat), label) for pat, label in _ANNOUNCEMENT_CONTENT_RULES
]


def is_announcement(title: str, text: str) -> bool:
    """回傳 True 表示此文章為財務公告格式文，應予過濾。"""
    for regex, _ in _COMPILED_ANNOUNCEMENT_CONTENT:
        if regex.search(text):
            return True
    return False


def announcement_reason(title: str, text: str) -> Optional[str]:
    """回傳命中的公告規則名稱（debug 用）；未命中回傳 None。"""
    for regex, label in _COMPILED_ANNOUNCEMENT_CONTENT:
        if regex.search(text):
            return f"content:{label}"
    return None


def filter_announcements_dataframe(df, title_col: str = "ArticleTitle", text_col: str = "ArticleText"):
    """從 DataFrame 移除財務公告格式文，回傳 (clean_df, n_removed)。"""
    mask = df.apply(lambda r: is_announcement(str(r[title_col]), str(r[text_col])), axis=1)
    n_removed = int(mask.sum())
    return df[~mask].reset_index(drop=True), n_removed


# ── 獨立執行：驗證規則效果 ───────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("articles.csv", encoding="utf-8-sig")
    clean_df, n_removed = filter_dataframe(df)

    print(f"原始文章數:   {len(df):,}")
    print(f"過濾雜訊數:   {n_removed:,}  ({n_removed/len(df)*100:.2f}%)")
    print(f"保留文章數:   {len(clean_df):,}")

    # 抽樣展示被過濾的文章
    noise_df = df[df.apply(lambda r: is_noise(str(r["ArticleTitle"]), str(r["ArticleText"])), axis=1)]
    print(f"\n被過濾文章範例（前 10 筆）：")
    for _, row in noise_df.head(10).iterrows():
        reason = noise_reason(str(row["ArticleTitle"]), str(row["ArticleText"]))
        print(f"  [{reason}] {row['ArticleTitle'][:60]}")
