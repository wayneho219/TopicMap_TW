#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick start - verify project is ready to run."""

import subprocess
import sys
import sqlite3
from pathlib import Path
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / 'data' / 'tw_stock_list.sqlite3'

def check_db():
    """Quick database check."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tw_stock_list")
        stocks = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM nlp_topics")
        topics = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM nlp_topic_stocks")
        assocs = c.fetchone()[0]
        conn.close()

        print(f"Database check: OK")
        print(f"  tw_stock_list: {stocks} stocks")
        print(f"  nlp_topics: {topics} topics")
        print(f"  nlp_topic_stocks: {assocs} associations")
        return True
    except Exception as e:
        print(f"Database check: FAILED ({e})")
        return False

def test_backend():
    """Test backend endpoints."""
    print(f"\nStarting backend test...")
    import time
    import requests

    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--port', '8000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT
    )

    time.sleep(3)

    try:
        r = requests.get('http://localhost:8000/api/market/hot?limit=1', timeout=5)
        if r.status_code == 200:
            print(f"Backend test: OK")
            return True
        else:
            print(f"Backend test: FAILED (HTTP {r.status_code})")
            return False
    except Exception as e:
        print(f"Backend test: FAILED ({str(e)[:50]})")
        return False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()

def main():
    print("=" * 60)
    print("EventCorr Quick Start Check")
    print("=" * 60)
    print()

    db_ok = check_db()

    if not db_ok:
        print("\nDatabase not initialized!")
        print("Run: python init_project.py")
        return 1

    try:
        backend_ok = test_backend()
    except ImportError:
        print("\nWarning: requests library not found (needed for test)")
        backend_ok = True

    print()
    print("=" * 60)
    if db_ok and backend_ok:
        print("Ready to run! Execute:")
        print()
        print("  Backend:  uvicorn backend.main:app --reload --port 8000")
        print("  Frontend: cd frontend && npm run dev")
        print()
        print("Then visit http://localhost:5173")
        print("=" * 60)
        return 0
    else:
        print("Something is not ready. Check errors above.")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())

    
#後端:uvicorn backend.main:app --reload --port 8000
#前端:npm run dev
