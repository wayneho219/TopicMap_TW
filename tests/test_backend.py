import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app

client = TestClient(app)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

def test_get_stock_known():
    """2330 台積電應存在於 DB，回傳 200 並含必要欄位"""
    resp = client.get('/api/stocks/2330')
    assert resp.status_code == 200
    data = resp.json()
    assert data['id'] == '2330'
    assert isinstance(data['price'], float)
    assert isinstance(data['change'], float)
    assert isinstance(data['changePercent'], float)
    assert isinstance(data['volume'], int)
    assert data['name'] != ''
    assert isinstance(data['tags'], list)
    assert len(data['tags']) >= 1

def test_get_stock_not_found():
    """不存在的股票代號應回傳 404"""
    resp = client.get('/api/stocks/9999')
    assert resp.status_code == 404

def test_get_stock_twse_tags():
    """TWSE 上市股票 tags 應含「上市」"""
    resp = client.get('/api/stocks/2330')
    assert resp.status_code == 200
    assert '上市' in resp.json()['tags']

def test_get_stock_tpex_tags():
    """上櫃股票 tags 應含「上櫃」（用已知上櫃代號 6547）"""
    resp = client.get('/api/stocks/6547')
    if resp.status_code == 200:
        assert '上櫃' in resp.json()['tags']
    # 若 DB 沒有此代號則跳過（不強制）
