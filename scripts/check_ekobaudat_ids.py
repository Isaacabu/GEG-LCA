import sqlite3

ids = [8, 354, 1332, 1312, 1108, 352, 661, 603, 604, 609, 610, 1049]

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

for material_id in ids:
    cur.execute(
        'SELECT id, name, u_value, category FROM dashboard_ekobaudatmaterial WHERE id = ?;',
        (material_id,),
    )
    print(cur.fetchone())

conn.close()
