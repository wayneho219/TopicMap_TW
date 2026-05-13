import sqlite3

conn = sqlite3.connect('data/tw_stock_list.sqlite3')
cursor = conn.cursor()

# Check table count
cursor.execute('SELECT COUNT(*) FROM tw_stock_list')
count = cursor.fetchone()[0]
print(f'tw_stock_list rows: {count}')

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'Tables: {[t[0] for t in tables]}')

# Check first few rows
cursor.execute('SELECT stock_code, stock_name, close_price FROM tw_stock_list LIMIT 3')
rows = cursor.fetchall()
print(f'Sample rows: {rows}')

conn.close()
