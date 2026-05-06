"""
PTT 版規雜訊過濾模組
====================
用途：在 topic_model.py Step 1 載入 articles.csv 後，過濾掉版規/論壇管理類雜訊。
財務公告類（月營收、財報、股利）不在此過濾範圍。

使用方式：
    from filter import is_noise
    df = df[~df.apply(lambda r: is_noise(r["ArticleTitle"], r["ArticleText"]), axis=1)]
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
    """
    從 DataFrame 移除雜訊列，回傳 (clean_df, n_removed)。
    不修改原 DataFrame。
    """
    mask = df.apply(lambda r: is_noise(str(r[title_col]), str(r[text_col])), axis=1)
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
