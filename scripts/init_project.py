#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive project initialization script."""

import os
import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
REQUIRED_FILES = {
    'output/result_all.csv': 'Topic modeling results',
    'data/tw_stocks.csv': 'Taiwan stock list reference',
}

def check_dependencies():
    """Check if all Python packages are installed."""
    print("🔍 Checking dependencies...")
    try:
        import requests
        import pandas
        import sqlite3
        print("✓ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("📦 Run: pip install -r requirements.txt")
        return False

def check_required_files():
    """Check if required input files exist."""
    print("\n🔍 Checking required files...")
    missing = []
    for file_path, desc in REQUIRED_FILES.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size / 1024
            print(f"✓ {file_path} ({size:.1f} KB) - {desc}")
        else:
            print(f"✗ {file_path} - MISSING: {desc}")
            missing.append(file_path)
    return len(missing) == 0, missing

def run_script(script_name, description):
    """Run a Python script and report results."""
    print(f"\n📦 {description}...")
    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        print(f"✗ Script not found: {script_name}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"✓ {description} completed")
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            return True
        else:
            print(f"✗ {description} failed")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱ {description} timed out (>120s)")
        return False
    except Exception as e:
        print(f"✗ {description} error: {e}")
        return False

def verify_database():
    """Verify database tables were created."""
    print("\n🔍 Verifying database...")
    import sqlite3

    db_path = PROJECT_ROOT / 'data' / 'tw_stock_list.sqlite3'
    if not db_path.exists():
        print("✗ Database not created")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Database tables: {', '.join(tables)}")

        # Check row counts
        for table in ['tw_stock_list', 'nlp_topics', 'nlp_topic_stocks']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = '✓' if count > 0 else '⚠'
                print(f"  {status} {table}: {count} rows")

        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

def main():
    print("=" * 60)
    print("EventCorr 專案初始化")
    print("=" * 60)

    # Step 1: Check dependencies
    if not check_dependencies():
        return 1

    # Step 2: Check required files
    files_ok, missing = check_required_files()
    if not files_ok:
        print(f"\n❌ Missing files needed for initialization:")
        for f in missing:
            print(f"  - {f}")
        print("\n請先執行以下步驟：")
        if 'output/result_all.csv' in missing:
            print("  1. python topic_model.py (Phase 1 + Phase 2)")
        if 'data/tw_stocks.csv' in missing:
            print("  2. python transform.py")
        return 1

    # Step 3: Initialize stock list from API
    if not run_script('scripts/tw_stock_list_sync.py', 'Syncing stock list from TWSE/TPEx API'):
        print("\n⚠ Stock list sync failed (network issue?) - this is not critical")

    # Step 4: Sync latest quotes
    if not run_script('scripts/tw_stock_quote_sync.py', 'Syncing latest stock quotes'):
        print("\n⚠ Quote sync failed (network issue?) - using cached data if available")

    # Step 5: Import NLP topics
    if not run_script('scripts/import_nlp_topics.py', 'Importing NLP topics from result_all.csv'):
        return 1

    # Step 6: Verify
    if not verify_database():
        print("\n❌ Database verification failed")
        return 1

    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n接下來可以運行：")
    print("  Frontend: cd frontend && npm run dev")
    print("  Backend:  uvicorn backend.main:app --reload --port 8000")
    print("\n訪問 http://localhost:5173")
    return 0

if __name__ == '__main__':
    sys.exit(main())
