import os
import sqlite3
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

def _seed_main(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE tw_stock_list (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL DEFAULT '',
            industry_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            source_as_of TEXT NOT NULL DEFAULT '',
            synced_at TEXT NOT NULL DEFAULT '',
            close_price REAL,
            change_val TEXT,
            change_pct TEXT,
            volume INTEGER
        );
        CREATE TABLE nlp_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT NOT NULL,
            parent_id INTEGER,
            total_invested REAL NOT NULL DEFAULT 0,
            article_count INTEGER NOT NULL DEFAULT 0,
            stock_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE nlp_topic_stocks (
            topic_id INTEGER NOT NULL,
            stock_code TEXT NOT NULL,
            PRIMARY KEY (topic_id, stock_code)
        );
        CREATE TABLE nlp_topic_industry_map (
            topic_id       INTEGER PRIMARY KEY,
            is_industry    INTEGER NOT NULL DEFAULT 0,
            major_industry TEXT,
            classified_at  TEXT NOT NULL
        );
        INSERT INTO tw_stock_list(stock_code, stock_name, industry_name, close_price, change_val, change_pct, volume)
            VALUES
            ('2330','台積電','半導體',1000.0,'+35','+3.50%',42000000),
            ('2454','聯發科','半導體', 800.0,'+10','+1.25%',10000000),
            ('3481','群創',  '電腦週邊', 15.0,'-0.5','-3.23%', 5000000),
            ('9990','測試甲','電腦週邊', 50.0,'-1',  '-2.00%', 1000000);
        INSERT INTO nlp_topics VALUES (1,'AI伺服器','fine',NULL,100000,10,2);
        INSERT INTO nlp_topic_stocks VALUES (1,'2330');
        INSERT INTO nlp_topic_stocks VALUES (1,'2454');
        INSERT INTO nlp_topic_industry_map VALUES (1,1,'半導體','2026-01-01T00:00:00');
    ''')
    conn.commit()
    conn.close()

def _seed_chain(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE tpex_industry_chain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_industry TEXT NOT NULL,
            chain_ic TEXT NOT NULL,
            chain_topic TEXT NOT NULL,
            segment_code TEXT NOT NULL,
            segment_name TEXT NOT NULL,
            listing_bucket TEXT NOT NULL DEFAULT '',
            stock_code TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        );
        INSERT INTO tpex_industry_chain(major_industry,chain_ic,chain_topic,segment_code,segment_name,stock_code,stock_name,scraped_at)
            VALUES
            ('半導體','D000','IC設計','D001','IC設計','2454','聯發科','2026-01-01'),
            ('半導體','D000','IC設計','D001','IC設計','2330','台積電','2026-01-01'),
            ('電腦週邊','F000','主機板','F001','主機板','3481','群創','2026-01-01'),
            ('電腦週邊','F000','主機板','F001','主機板','9990','測試甲','2026-01-01');
    ''')
    conn.commit()
    conn.close()

@pytest.fixture
def client(tmp_path):
    main_db   = str(tmp_path / 'main.sqlite3')
    chain_db  = str(tmp_path / 'chain.sqlite3')
    _seed_main(main_db)
    _seed_chain(chain_db)

    import backend.main as m
    orig_db       = m.DB_PATH
    orig_chain_db = m.DB_CHAIN_PATH
    m.DB_PATH       = main_db
    m.DB_CHAIN_PATH = chain_db
    yield TestClient(m.app)
    m.DB_PATH       = orig_db
    m.DB_CHAIN_PATH = orig_chain_db

# ── /api/market/industries ──────────────────────────────────────

def test_get_industries_returns_list(client):
    r = client.get('/api/market/industries')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = [item['name'] for item in data]
    assert '半導體' in names
    semi = next(item for item in data if item['name'] == '半導體')
    assert 'topicCount' in semi
    assert 'advance' in semi
    assert 'decline' in semi
    assert 'changePercent' in semi
    assert 'totalVolume' in semi
    # 2330 vol=42000000, 2454 vol=10000000
    assert semi['totalVolume'] == 52000000

def test_get_industries_topic_count_includes_nlp(client):
    r = client.get('/api/market/industries')
    data = r.json()
    semi = next(item for item in data if item['name'] == '半導體')
    # chain_topic: IC設計 = 1, NLP: AI伺服器 = 1 → total 2
    assert semi['topicCount'] == 2

def test_get_industries_advance_decline(client):
    r = client.get('/api/market/industries')
    data = r.json()
    semi = next(item for item in data if item['name'] == '半導體')
    # 2330 +3.50%, 2454 +1.25% → advance=2, decline=0
    assert semi['advance'] == 2
    assert semi['decline'] == 0

def test_get_industries_sort_order(client):
    r = client.get('/api/market/industries?sort=change&order=desc')
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # desc: 半導體 avg +2.375% > 電腦週邊 avg -2.615%
    assert data[0]['changePercent'] >= data[1]['changePercent']

    r2 = client.get('/api/market/industries?sort=change&order=asc')
    data2 = r2.json()
    assert data2[0]['changePercent'] <= data2[1]['changePercent']

def test_get_industries_sort_by_volume(client):
    r = client.get('/api/market/industries?sort=volume&order=desc')
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # 半導體 total 52000000 > 電腦週邊 total 6000000
    assert data[0]['name'] == '半導體'
    assert data[0]['totalVolume'] >= data[1]['totalVolume']

    r2 = client.get('/api/market/industries?sort=volume&order=asc')
    data2 = r2.json()
    assert data2[0]['totalVolume'] <= data2[1]['totalVolume']

# ── /api/market/industry/{name}/topics ──────────────────────────

def test_get_industry_topics_contains_tpex(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    assert r.status_code == 200
    data = r.json()
    names = [t['name'] for t in data]
    # IC設計 is for 半導體 stocks (2330, 2454)
    assert 'IC設計' in names
    # 主機板 is for 電腦週邊 stocks — should NOT appear under 半導體
    assert '主機板' not in names

def test_get_industry_topics_contains_nlp(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    data = r.json()
    nlp_items = [t for t in data if t['source'] == 'nlp']
    assert len(nlp_items) == 1
    assert nlp_items[0]['name'] == 'AI伺服器'

def test_get_industry_topics_source_field(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    assert r.status_code == 200
    data = r.json()
    for t in data:
        assert t['source'] in ('tpex', 'nlp')
        assert 'changePercent' in t
        assert 'stockCount' in t

def test_get_industry_topics_unknown_returns_empty(client):
    r = client.get('/api/market/industry/%E4%B8%8D%E5%AD%98%E5%9C%A8/topics')
    assert r.status_code == 200
    assert r.json() == []
