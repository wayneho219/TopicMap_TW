#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize tw_stock_list table from local tw_stocks.csv."""

import sqlite3
import pandas as pd
from pathlib import Path
import datetime
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
CSV_PATH = PROJECT_ROOT / 'data' / 'tw_stocks.csv'
DB_PATH = PROJECT_ROOT / 'data' / 'tw_stock_list.sqlite3'

INDUSTRY_CODE_MAP = {
    "01": "水泥工業",
    "02": "食品工業",
    "03": "塑膠工業",
    "04": "紡織纖維",
    "05": "電機機械",
    "06": "電器電纜",
    "08": "玻璃陶瓷",
    "09": "造紙工業",
    "10": "鋼鐵工業",
    "11": "橡膠工業",
    "12": "汽車工業",
    "14": "建材營造",
    "15": "航運業",
    "16": "觀光餐旅",
    "17": "金融保險",
    "18": "貿易百貨",
    "19": "綜合",
    "20": "其他",
    "21": "化學工業",
    "22": "生技醫療業",
    "23": "油電燃氣業",
    "24": "半導體業",
    "25": "電腦及週邊設備業",
    "26": "光電業",
    "27": "通信網路業",
    "28": "電子零組件業",
    "29": "電子通路業",
    "30": "資訊服務業",
    "31": "其他電子業",
    "32": "文化創意業",
    "33": "農業科技業",
    "34": "電子商務",
    "35": "綠能環保",
    "36": "數位雲端",
    "37": "運動休閒",
    "38": "居家生活",
}

def init_tw_stock_list():
    if not CSV_PATH.exists():
        print(f"Error: File not found: {CSV_PATH}")
        return False

    # Read CSV
    df = pd.read_csv(CSV_PATH, dtype={'stock_code': str})
    print(f"Loaded {len(df)} stocks from tw_stocks.csv")

    # Initialize database
    conn = sqlite3.connect(DB_PATH)
    try:
        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tw_stock_list (
                stock_code    TEXT PRIMARY KEY,
                stock_name    TEXT NOT NULL,
                market        TEXT NOT NULL,
                industry_code TEXT NOT NULL DEFAULT '',
                industry_name TEXT NOT NULL DEFAULT '',
                close_price   REAL DEFAULT NULL,
                open_price    REAL DEFAULT NULL,
                high_price    REAL DEFAULT NULL,
                low_price     REAL DEFAULT NULL,
                change_val    TEXT DEFAULT NULL,
                change_pct    TEXT DEFAULT NULL,
                volume        INTEGER DEFAULT 0,
                source_url    TEXT NOT NULL,
                source_as_of  TEXT NOT NULL DEFAULT '',
                synced_at     TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_stock_market ON tw_stock_list (market)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_stock_industry ON tw_stock_list (industry_code)")

        # Clear old data
        conn.execute("DELETE FROM tw_stock_list")

        # Insert data from CSV
        for _, row in df.iterrows():
            stock_code = str(row['stock_code']).strip()
            stock_name = str(row['stock_name']).strip()
            market = str(row['market']).strip()
            industry_code = str(row['industry_code']).strip() if not pd.isna(row['industry_code']) else ''
            industry_name = str(row['industry_name']).strip() if not pd.isna(row['industry_name']) else ''
            close_price = float(row['close_price']) if not pd.isna(row['close_price']) else None
            change_val = str(row['change_val']).strip() if not pd.isna(row['change_val']) else None
            change_pct = str(row['change_pct']).strip() if not pd.isna(row['change_pct']) else None
            volume = int(row['volume']) if not pd.isna(row['volume']) else 0
            source_url = str(row['source_url']).strip() if not pd.isna(row['source_url']) else ''
            source_as_of = str(row['source_as_of']).strip() if not pd.isna(row['source_as_of']) else ''
            synced_at = str(row['synced_at']).strip() if not pd.isna(row['synced_at']) else datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            conn.execute("""
                INSERT OR REPLACE INTO tw_stock_list
                (stock_code, stock_name, market, industry_code, industry_name, close_price,
                 change_val, change_pct, volume, source_url, source_as_of, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_code, stock_name, market, industry_code, industry_name, close_price,
                  change_val, change_pct, volume, source_url, source_as_of, synced_at))

        conn.commit()
        print(f"Success: Inserted {len(df)} stocks into tw_stock_list table")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    init_tw_stock_list()
