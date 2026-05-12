import sqlite3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from unittest.mock import patch, MagicMock


def _make_response(text: str):
    resp = MagicMock()
    resp.content = [MagicMock(text=text)]
    return resp


def test_classify_topic_industry():
    import scripts.classify_nlp_topics as c
    with patch.object(c.client.messages, 'create',
                      return_value=_make_response('{"is_industry": true, "major_industry": "半導體"}')):
        result = c.classify_topic('台積電股')
    assert result['is_industry'] is True
    assert result['major_industry'] == '半導體'


def test_classify_topic_noise():
    import scripts.classify_nlp_topics as c
    with patch.object(c.client.messages, 'create',
                      return_value=_make_response('{"is_industry": false, "major_industry": null}')):
        result = c.classify_topic('個股閒聊')
    assert result['is_industry'] is False
    assert result['major_industry'] is None


def test_run_incremental(tmp_path):
    db = str(tmp_path / 'test.sqlite3')
    conn = sqlite3.connect(db)
    conn.executescript('''
        CREATE TABLE nlp_topics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            level TEXT NOT NULL
        );
        CREATE TABLE nlp_topic_industry_map (
            topic_id       INTEGER PRIMARY KEY,
            is_industry    INTEGER NOT NULL DEFAULT 0,
            major_industry TEXT,
            classified_at  TEXT NOT NULL
        );
        INSERT INTO nlp_topics VALUES (1,'台積電股','fine');
        INSERT INTO nlp_topics VALUES (2,'個股閒聊','fine');
        INSERT INTO nlp_topics VALUES (3,'medium主題','medium');
        -- topic_id=2 already classified; should be skipped
        INSERT INTO nlp_topic_industry_map VALUES (2,0,NULL,'2026-01-01');
    ''')
    conn.commit()
    conn.close()

    import scripts.classify_nlp_topics as c
    original_db = c.DB_PATH
    c.DB_PATH = db
    try:
        with patch.object(c.client.messages, 'create',
                          return_value=_make_response('{"is_industry": true, "major_industry": "半導體"}')):
            c.run()
    finally:
        c.DB_PATH = original_db

    conn2 = sqlite3.connect(db)
    rows = conn2.execute('SELECT topic_id, is_industry, major_industry FROM nlp_topic_industry_map ORDER BY topic_id').fetchall()
    conn2.close()
    # Only topic_id=1 (fine, unclassified) should be newly inserted; topic_id=2 unchanged; topic_id=3 (medium) skipped
    assert len(rows) == 2
    assert rows[0] == (1, 1, '半導體')
    assert rows[1] == (2, 0, None)
