# tests/test_topics_api.py
import os
import sqlite3
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

def _seed(path: str):
    conn = sqlite3.connect(path)
    conn.executescript('''
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
            article_count INTEGER NOT NULL DEFAULT 0,
            total_invested REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (topic_id, stock_code)
        );
        CREATE TABLE tw_stock_list (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL DEFAULT '',
            industry_code TEXT NOT NULL DEFAULT '',
            industry_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            source_as_of TEXT NOT NULL DEFAULT '',
            synced_at TEXT NOT NULL DEFAULT '',
            close_price REAL,
            change_val TEXT,
            change_pct TEXT,
            volume INTEGER,
            quote_date TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL
        );
        INSERT INTO nlp_topics VALUES (1,'AI半導體','medium',NULL,854467864250.49,187,25);
        INSERT INTO nlp_topics VALUES (2,'高股息','medium',NULL,174688926965.03,160,30);
        INSERT INTO nlp_topics VALUES (3,'台積電股','fine',1,461413362216.5,42,1);
        INSERT INTO nlp_topics VALUES (4,'消費電子','fine',1,344648974867.14,35,8);
        INSERT INTO nlp_topic_stocks VALUES (1,'2330',42,461413362216.5);
        INSERT INTO nlp_topic_stocks VALUES (3,'2330',42,461413362216.5);
        INSERT INTO tw_stock_list(stock_code,stock_name,close_price,change_val,change_pct,volume)
            VALUES ('2330','台積電',1000.0,'+35','+3.50%',42000000);
    ''')
    conn.commit()
    conn.close()

@pytest.fixture
def client(tmp_path):
    db = str(tmp_path / 'test.sqlite3')
    _seed(db)
    import backend.main as m
    original = m.DB_PATH
    m.DB_PATH = db
    yield TestClient(m.app)
    m.DB_PATH = original

def test_get_topics_medium_sorted(client):
    r = client.get('/api/topics?level=medium')
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]['name'] == 'AI半導體'
    assert data[0]['totalInvested'] == pytest.approx(854467864250.49)
    assert data[0]['articleCount'] == 187
    assert data[0]['stockCount'] == 25

def test_get_topics_fine(client):
    r = client.get('/api/topics?level=fine')
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_get_topic_children(client):
    r = client.get('/api/topics/AI半導體/children')
    assert r.status_code == 200
    children = r.json()
    assert len(children) == 2
    assert children[0]['name'] == '台積電股'
    assert children[0]['level'] == 'fine'

def test_get_topic_children_not_found(client):
    r = client.get('/api/topics/不存在主題/children')
    assert r.status_code == 404

def test_get_topic_stocks_heat(client):
    r = client.get('/api/topics/AI半導體/stocks?level=medium&sort=heat')
    assert r.status_code == 200
    stocks = r.json()
    assert len(stocks) == 1
    s = stocks[0]
    assert s['id'] == '2330'
    assert s['name'] == '台積電'
    assert isinstance(s['price'], float)
    assert s['articleCount'] == 42
    assert s['topicInvested'] == pytest.approx(461413362216.5)

def test_get_topic_stocks_not_found(client):
    r = client.get('/api/topics/不存在主題/stocks')
    assert r.status_code == 404

def test_get_topics_invalid_level(client):
    r = client.get('/api/topics?level=invalid')
    assert r.status_code == 400
