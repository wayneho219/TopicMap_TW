# scripts/import_nlp_topics.py
import os
import sqlite3
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'output', 'result_all.csv')
DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

_DDL = '''
DROP TABLE IF EXISTS nlp_topic_stocks;
DROP TABLE IF EXISTS nlp_topics;

CREATE TABLE nlp_topics (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    level          TEXT    NOT NULL CHECK(level IN ('medium', 'fine')),
    parent_id      INTEGER REFERENCES nlp_topics(id),
    total_invested REAL    NOT NULL DEFAULT 0,
    article_count  INTEGER NOT NULL DEFAULT 0,
    stock_count    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_nlp_topics_level  ON nlp_topics(level);
CREATE INDEX idx_nlp_topics_parent ON nlp_topics(parent_id);

CREATE TABLE nlp_topic_stocks (
    topic_id       INTEGER NOT NULL REFERENCES nlp_topics(id) ON DELETE CASCADE,
    stock_code     TEXT    NOT NULL,
    article_count  INTEGER NOT NULL DEFAULT 0,
    total_invested REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (topic_id, stock_code)
);
CREATE INDEX idx_nlp_topic_stocks_code ON nlp_topic_stocks(stock_code);
'''

def import_nlp_topics(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"result_all.csv not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'stock_id': str})
    df['invested_amount'] = pd.to_numeric(df['invested_amount'], errors='coerce').fillna(0)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_DDL)

        # ── medium 主題 ────────────────────────────────────────────────────────
        med_stats = (
            df.groupby('label_medium')
            .agg(
                total_invested=('invested_amount', 'sum'),
                article_count=('label_medium', 'count'),
                stock_count=('stock_id', 'nunique'),
            )
            .reset_index()
        )
        medium_id: dict[str, int] = {}
        for _, row in med_stats.iterrows():
            cur = conn.execute(
                'INSERT INTO nlp_topics (name, level, parent_id, total_invested, article_count, stock_count) '
                'VALUES (?,?,?,?,?,?)',
                (row['label_medium'], 'medium', None,
                 float(row['total_invested']), int(row['article_count']), int(row['stock_count'])),
            )
            medium_id[row['label_medium']] = cur.lastrowid

        # ── fine 主題 ──────────────────────────────────────────────────────────
        fine_stats = (
            df.groupby(['label_medium', 'label_fine'])
            .agg(
                total_invested=('invested_amount', 'sum'),
                article_count=('label_fine', 'count'),
                stock_count=('stock_id', 'nunique'),
            )
            .reset_index()
        )
        fine_id: dict[tuple, int] = {}
        for _, row in fine_stats.iterrows():
            parent = medium_id[row['label_medium']]
            cur = conn.execute(
                'INSERT INTO nlp_topics (name, level, parent_id, total_invested, article_count, stock_count) '
                'VALUES (?,?,?,?,?,?)',
                (row['label_fine'], 'fine', parent,
                 float(row['total_invested']), int(row['article_count']), int(row['stock_count'])),
            )
            fine_id[(row['label_medium'], row['label_fine'])] = cur.lastrowid

        # ── medium × stock ────────────────────────────────────────────────────
        for med, grp in df.groupby('label_medium'):
            topic_id = medium_id[med]
            for sid, sgrp in grp.groupby('stock_id'):
                conn.execute(
                    'INSERT INTO nlp_topic_stocks (topic_id, stock_code, article_count, total_invested) '
                    'VALUES (?,?,?,?)',
                    (topic_id, str(sid), len(sgrp), float(sgrp['invested_amount'].sum())),
                )

        # ── fine × stock ──────────────────────────────────────────────────────
        for (med, fine), grp in df.groupby(['label_medium', 'label_fine']):
            topic_id = fine_id[(med, fine)]
            for sid, sgrp in grp.groupby('stock_id'):
                conn.execute(
                    'INSERT INTO nlp_topic_stocks (topic_id, stock_code, article_count, total_invested) '
                    'VALUES (?,?,?,?)',
                    (topic_id, str(sid), len(sgrp), float(sgrp['invested_amount'].sum())),
                )

        conn.commit()
        n_med = len(medium_id)
        n_fine = len(fine_id)
        print(f"匯入完成：{n_med} 個 medium 主題，{n_fine} 個 fine 主題")
    finally:
        conn.close()


if __name__ == '__main__':
    import_nlp_topics()
