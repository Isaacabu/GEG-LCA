import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM dashboard_ekobaudatmaterial')
total = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM dashboard_ekobaudatmaterial WHERE u_value IS NOT NULL')
with_u = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM dashboard_ekobaudatmaterial WHERE (LOWER(name) LIKE '%fenster%' OR LOWER(category) LIKE '%fenster%' OR LOWER(name) LIKE '%glas%') AND u_value IS NOT NULL")
fen_with_u = c.fetchone()[0]

print('total', total)
print('with_u', with_u)
print('fen_with_u', fen_with_u)

conn.close()
