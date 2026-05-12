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
        INSERT INTO tw_stock_list(stock_code, stock_name, close_price, change_val, change_pct, volume)
            VALUES
            ('2330','台積電',1000.0,'+35','+3.50%',42000000),
            ('2454','聯發科', 800.0,'+10','+1.25%',10000000),
            ('3481','群創',  15.0,'-0.5','-3.23%', 5000000);
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
            ('半導體','D000','半導體','D001','IC設計','2454','聯發科','2026-01-01'),
            ('半導體','D000','半導體','D001','IC設計','2330','台積電','2026-01-01'),
            ('半導體','D000','晶圓代工','D002','晶圓廠','3481','群創','2026-01-01');
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
    assert len(data) == 1
    item = data[0]
    assert item['name'] == '半導體'
    assert 'topicCount' in item
    assert 'advance' in item
    assert 'decline' in item
    assert 'changePercent' in item

def test_get_industries_topic_count_includes_nlp(client):
    r = client.get('/api/market/industries')
    data = r.json()
    # chain_topics: 半導體, 晶圓代工 = 2, NLP: AI伺服器 = 1 → total 3
    assert data[0]['topicCount'] == 3

def test_get_industries_advance_decline(client):
    r = client.get('/api/market/industries')
    data = r.json()
    # 2330 +3.50%, 2454 +1.25% → advance=2; 3481 -3.23% → decline=1
    assert data[0]['advance'] == 2
    assert data[0]['decline'] == 1

def test_get_industries_sort_order(client):
    r = client.get('/api/market/industries?sort=change&order=desc')
    assert r.status_code == 200

# ── /api/market/industry/{name}/topics ──────────────────────────

def test_get_industry_topics_contains_tpex(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    assert r.status_code == 200
    data = r.json()
    names = [t['name'] for t in data]
    assert '半導體' in names
    assert '晶圓代工' in names

def test_get_industry_topics_contains_nlp(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    data = r.json()
    nlp_items = [t for t in data if t['source'] == 'nlp']
    assert len(nlp_items) == 1
    assert nlp_items[0]['name'] == 'AI伺服器'

def test_get_industry_topics_source_field(client):
    r = client.get('/api/market/industry/%E5%8D%8A%E5%B0%8E%E9%AB%94/topics')
    data = r.json()
    for t in data:
        assert t['source'] in ('tpex', 'nlp')
        assert 'changePercent' in t
        assert 'stockCount' in t

def test_get_industry_topics_unknown_returns_empty(client):
    r = client.get('/api/market/industry/%E4%B8%8D%E5%AD%98%E5%9C%A8/topics')
    assert r.status_code == 200
    assert r.json() == []
