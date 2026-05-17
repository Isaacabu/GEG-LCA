import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fenster%';")
print(cur.fetchall())
for table in ['dashboard_fenstertyp', 'dashboard_ekobaudatmaterial']:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
    if cur.fetchone():
        print('TABLE', table)
        cur.execute(f'SELECT * FROM {table} LIMIT 10;')
        for row in cur.fetchall():
            print(row)
conn.close()
