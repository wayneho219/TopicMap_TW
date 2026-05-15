"""
Update tw_stock_list.sqlite3 with data from output/result_all.csv

This script:
1. Reads result_all.csv (output from topic_model.py Phase 2)
2. Aggregates data by stock_id (latest price, volume, etc.)
3. Updates tw_stock_list table with label_medium and label_fine columns
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Paths
DB_PATH = Path('data/tw_stock_list.sqlite3')
CSV_PATH = Path('output/result_all.csv')

if not CSV_PATH.exists():
    print(f"ERROR: {CSV_PATH} not found")
    exit(1)

# Read CSV
print(f"Reading {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")

# Group by stock_id and take the most recent row (by ArticleCreateTime)
# This ensures we get the latest price/volume for each stock
df['ArticleCreateTime'] = pd.to_datetime(df['ArticleCreateTime'])
df_latest = df.sort_values('ArticleCreateTime').groupby('stock_id').tail(1)
print(f"\nAggregated to {len(df_latest)} unique stocks")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if label columns exist, if not create them
print("\nChecking database schema...")
cursor.execute("PRAGMA table_info(tw_stock_list)")
columns = {row[1] for row in cursor.fetchall()}

new_columns = []
if 'label_medium' not in columns:
    cursor.execute("ALTER TABLE tw_stock_list ADD COLUMN label_medium TEXT")
    new_columns.append('label_medium')
    print("Added column: label_medium")

if 'label_fine' not in columns:
    cursor.execute("ALTER TABLE tw_stock_list ADD COLUMN label_fine TEXT")
    new_columns.append('label_fine')
    print("Added column: label_fine")

if new_columns:
    conn.commit()
    print(f"Created {len(new_columns)} new column(s)")

# Update tw_stock_list with labels from result_all.csv
print("\nUpdating tw_stock_list with labels...")
updated_count = 0

for _, row in df_latest.iterrows():
    stock_id = str(int(row['stock_id']))  # Ensure it's a string
    label_medium = row['label_medium'] if pd.notna(row['label_medium']) else None
    label_fine = row['label_fine'] if pd.notna(row['label_fine']) else None

    # Update the first matching stock_code
    cursor.execute(
        '''
        UPDATE tw_stock_list
        SET label_medium = ?, label_fine = ?
        WHERE stock_code = ?
        ''',
        (label_medium, label_fine, stock_id)
    )

    if cursor.rowcount > 0:
        updated_count += 1

conn.commit()
print(f"Updated {updated_count} stocks")

# Show summary
print("\nSample updated records:")
cursor.execute('''
    SELECT stock_code, stock_name, label_medium, label_fine
    FROM tw_stock_list
    WHERE label_medium IS NOT NULL
    LIMIT 5
''')
for row in cursor.fetchall():
    print(f"  {row[0]} {row[1]}: {row[2]} / {row[3]}")

conn.close()
print("\nDone!")
