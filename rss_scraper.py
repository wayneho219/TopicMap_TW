import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
import os

# ── 設定區 ────────────────────────────────────────────────────────────────────
PTT_BASE      = "https://www.ptt.cc"
<<<<<<< HEAD
PTT_BOARDS    = ["Stock"]
MAX_PER_STOCK = 10

STOPWORDS = [

    # ===== 法人買賣超 =====
    "買超","賣超","外資","投信",
    "自營商","排行","張數",
    "收盤價","漲跌","百萬",

    # ===== 月營收公告 =====
    "去年同期","累計","增減",
    "本月","去年","營收",
    "收入","百分比","自結",

    # ===== 財報公告 =====
    "每股盈餘","EPS","稅前",
    "稅後","淨利","損益","現金股利"

    # ===== 公告垃圾 =====
    "公開資訊觀測站","MOPS",
    "TWSE","證交所","櫃買中心",
    "重大訊息","公告",

    # ===== 注意股 =====
    "注意交易資訊",
    "有價證券",
    "達公布標準",

    # ===== 股票抽籤 =====
    "申購","承銷","承銷價",
    "扣款日","抽籤日","進場","退場"

=======
PTT_BOARDS    = ["Stock"]  # 要爬的看板，可加 "StockForum" 等
MAX_PER_STOCK = 10          # 每支股票最多保留幾篇
STOPWORDS = [
    # 法人買賣超
    "買超", "賣超", "外資", "投信", "自營商", "排行", "張數", "收盤價", "漲跌", "百萬",
    # 月營收公告
    "去年同期", "累計", "增減", "本月", "去年", "營收", "收入", "百分比", "自結",
    # 財報公告
    "每股盈餘", "EPS", "稅前", "稅後", "淨利", "損益", "現金股利",
    # 公告垃圾
    "公開資訊觀測站", "MOPS", "TWSE", "證交所", "櫃買中心", "重大訊息", "公告",
    # 注意股
    "注意交易資訊", "有價證券", "達公布標準",
    # 股票抽籤
    "申購", "承銷", "承銷價", "扣款日", "抽籤日", "進場", "退場",
>>>>>>> main
]

_SESSION = requests.Session()
_SESSION.cookies.set("over18", "1")
_SESSION.headers.update({
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Referer":         "https://www.ptt.cc/bbs/Stock/index.html",
})


def _get(url: str, retries: int = 3) -> requests.Response | None:
    for attempt in range(1, retries + 1):
        try:
            resp = _SESSION.get(url, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  [WARN] 第 {attempt} 次請求失敗 {url}：{e}")
            if attempt < retries:
                time.sleep(2 * attempt)
    return None


def _contains_stopword(text: str) -> bool:
    """檢查標題或內文是否含有任何 stopword。"""
    return any(sw in text for sw in STOPWORDS)


def _iter_search_articles(board: str, query: str):
    """
    Generator：逐頁搜尋並逐篇 yield，讓外層可以按需取用，
    不需預先決定要抓幾篇，直到沒有更多頁才停止。
    """
    url = f"{PTT_BASE}/bbs/{board}/search?q={requests.utils.quote(query)}"

    while url:
        resp = _get(url)
        if resp is None:
            return

        soup = BeautifulSoup(resp.text, "html.parser")

        for row in soup.select("div.r-ent"):
            title_tag = row.select_one("div.title a")
            date_tag  = row.select_one("div.date")
            if not title_tag:
                continue
            yield {
                "title": title_tag.get_text(strip=True),
                "url":   PTT_BASE + title_tag["href"],
                "date":  date_tag.get_text(strip=True) if date_tag else "",
            }

        prev = soup.select_one("a.btn.wide:-soup-contains('上頁')")
        if prev and prev.get("href"):
            url = PTT_BASE + prev["href"]
            time.sleep(0.3)
        else:
            url = None  # 已到最舊一頁，結束


def _get_article_content(url: str) -> str:
    resp = _get(url)
    if resp is None:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.select_one("div#main-content")
    if not main:
        return ""

    for tag in main.select("div.article-metaline, div.article-metaline-right"):
        tag.decompose()
    for tag in main.select("div.push"):
        tag.decompose()

    content = main.get_text(separator="\n")
    content = re.split(r"\n--\s*\n", content)[0]
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    return content


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "stock_id", "ArticleTitle", "ArticleText", "ArticleCreateTime"
    ])


CHECKPOINT_FILE = "_ptt_checkpoint.json"


def _load_checkpoint() -> set[str]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return set(json.load(f).get("done", []))
    return set()


def _save_checkpoint(done: set[str]) -> None:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"done": list(done)}, f, ensure_ascii=False)


def _append_to_csv(rows: list[dict], output_path: str, write_header: bool) -> None:
    if not rows:
        return
    current_year = pd.Timestamp.now().year
    df = pd.DataFrame(rows)
    df["ArticleCreateTime"] = pd.to_datetime(
        df["ArticleCreateTime"].apply(lambda d: f"{current_year}/{d.strip()}"),
        format="%Y/%m/%d", errors="coerce"
    )
    df = df.drop_duplicates(subset=["stock_id", "_source_url"])
    df = df.drop(columns=["_source_url"])
    df.to_csv(
        output_path,
        mode="w" if write_header else "a",
        header=write_header,
        index=False,
        encoding="utf-8-sig",
    )


def fetch_and_process_ptt(
    stock_dict: dict,
    boards: list = PTT_BOARDS,
    max_per_stock: int = MAX_PER_STOCK,
    output_path: str = "articles.csv",
) -> pd.DataFrame:
    done_ids    = _load_checkpoint()
    seen_urls:  set[str] = set()
    first_write = not os.path.exists(output_path)

    total   = len(stock_dict)
    skipped = len(done_ids & stock_dict.keys())
    print(f"共 {total} 支股票，已完成 {skipped} 支，剩餘 {total - skipped} 支。")

    for i, stock_id in enumerate(stock_dict, 1):
        if stock_id in done_ids:
            print(f"  [{i}/{total}] {stock_id} 已完成，跳過。")
            continue

        batch: list[dict] = []

        for board in boards:
            if len(batch) >= max_per_stock:
                break

            print(f"  [{i}/{total}] 搜尋 [{board}] {stock_id}...")
            scanned = skipped_count = 0

            # generator：按需逐篇取用，自動翻頁直到滿額或無更多文章
            for art in _iter_search_articles(board, stock_id):
                if len(batch) >= max_per_stock:
                    break

                scanned += 1
                url = art["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # ── 標題過濾 ────────────────────────────────────────
                if _contains_stopword(art["title"]):
                    print(f"    [SKIP] 標題含停用詞：{art['title'][:40]}")
                    skipped_count += 1
                    continue

                content = _get_article_content(url)
                time.sleep(0.3)

<<<<<<< HEAD
                # ── 內文過濾 ────────────────────────────────────────
                if _contains_stopword(content):
                    print(f"    [SKIP] 內文含停用詞：{art['title'][:40]}")
                    skipped_count += 1
=======
                title = art["title"]
                if any(sw in title for sw in STOPWORDS):
>>>>>>> main
                    continue

                batch.append({
                    "stock_id":          stock_id,
                    "ArticleTitle":      art["title"],
                    "ArticleText":       content,
                    "ArticleCreateTime": art["date"],
                    "_source_url":       url,
                })
                print(f"    [OK {len(batch)}/{max_per_stock}] {art['title'][:40]}")

            print(f"    掃描 {scanned} 篇，略過 {skipped_count} 篇，收錄 {len(batch)} 篇。")
            if len(batch) < max_per_stock:
                print(f"    [WARN] PTT 已無更多文章，{stock_id} 最終僅收錄 {len(batch)} 篇。")

        _append_to_csv(batch, output_path, write_header=first_write)
        first_write = False
        print(f"    寫入 {len(batch)} 筆 → {output_path}")

        done_ids.add(stock_id)
        _save_checkpoint(done_ids)

    if done_ids >= stock_dict.keys():
        os.remove(CHECKPOINT_FILE)
        print(f"\n所有股票處理完畢，已清除斷點檔。")

    if os.path.exists(output_path):
        return pd.read_csv(output_path, encoding="utf-8-sig")
    return _empty_df()


def load_stock_dict_from_csv(csv_path: str) -> dict:
    df = pd.read_csv(csv_path, dtype=str).fillna("")

    if "stock_code" in df.columns:
        id_col = "stock_code"
    elif "stock_id" in df.columns:
        id_col = "stock_id"
    else:
        raise ValueError(f"{csv_path} 找不到 stock_code 或 stock_id 欄位，請確認欄位名稱。")

    stock_dict: dict = {}

    for _, row in df.iterrows():
        sid      = str(row[id_col]).strip()
        keywords = [sid]

        if "stock_name" in df.columns and row["stock_name"]:
            keywords.insert(0, str(row["stock_name"]).strip())

        if "stock_alias" in df.columns and row["stock_alias"]:
            aliases = [a.strip() for a in row["stock_alias"].split(",") if a.strip()]
            keywords.extend(aliases)

        stock_dict[sid] = list(dict.fromkeys(k for k in keywords if k))

    return stock_dict


if __name__ == "__main__":
    my_stock_dict = load_stock_dict_from_csv("data/tw_stocks.csv")
    output_path = "articles.csv"

    print("開始從 PTT 搜尋各股票文章...")
    result_df = fetch_and_process_ptt(my_stock_dict, output_path=output_path)

    print(f"\n完成！共 {len(result_df)} 筆資料已存至 {output_path}")